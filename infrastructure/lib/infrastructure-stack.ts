import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as cloudwatchActions from 'aws-cdk-lib/aws-cloudwatch-actions';

export class InfrastructureStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const projectName = 'serverless-stock-dashboard';
    const backendPath = path.join(__dirname, '../../backend');
    const frontendDistPath = path.join(__dirname, '../../frontend/dist');

    cdk.Tags.of(this).add('Project', 'ServerlessStockDashboard');
    cdk.Tags.of(this).add('ManagedBy', 'AWSCDK');

    const moversTable = new dynamodb.Table(this, 'MoversTable', {
      tableName: `${projectName}-movers`,
      partitionKey: {
        name: 'record_type',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'date',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const stockApiSecretName = 'stock-dashboard/api-key';

    const stockApiSecret = secretsmanager.Secret.fromSecretNameV2(
      this,
      'StockApiSecret',
      stockApiSecretName,
    );

    const ingestionLogGroup = new logs.LogGroup(this, 'IngestionLogGroup', {
      logGroupName: `/aws/lambda/${projectName}-ingestion`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const apiLogGroup = new logs.LogGroup(this, 'ApiLogGroup', {
      logGroupName: `/aws/lambda/${projectName}-api`,
      retention: logs.RetentionDays.ONE_WEEK,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const ingestionEnvironment = {
      TABLE_NAME: moversTable.tableName,
      SECRET_NAME: stockApiSecretName,
      MASSIVE_BASE_URL: 'https://api.massive.com',
      LOOKBACK_DAYS: '4',
    };

    const apiEnvironment = {
      TABLE_NAME: moversTable.tableName,
    };

    const ingestionFunction = new lambda.DockerImageFunction(this, 'IngestionFunction', {
      functionName: `${projectName}-ingestion`,
      code: lambda.DockerImageCode.fromImageAsset(backendPath, {
        file: 'Dockerfile.lambda',
        cmd: ['ingest.handler.lambda_handler'],
      }),
      architecture: lambda.Architecture.X86_64,
      timeout: cdk.Duration.seconds(120),
      memorySize: 512,
      environment: ingestionEnvironment,
      logGroup: ingestionLogGroup,
    });

    const apiFunction = new lambda.DockerImageFunction(this, 'ApiFunction', {
      functionName: `${projectName}-api`,
      code: lambda.DockerImageCode.fromImageAsset(backendPath, {
        file: 'Dockerfile.lambda',
        cmd: ['api.handler.lambda_handler'],
      }),
      architecture: lambda.Architecture.X86_64,
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: apiEnvironment,
      logGroup: apiLogGroup,
    });

    moversTable.grantWriteData(ingestionFunction);
    moversTable.grantReadData(apiFunction);
    stockApiSecret.grantRead(ingestionFunction);

    const dailyIngestionRule = new events.Rule(this, 'DailyIngestionRule', {
      ruleName: `${projectName}-daily-ingestion`,
      description: 'Runs the stock mover ingestion Lambda once per day',
      schedule: events.Schedule.cron({
        minute: '0',
        hour: '23',
      }),
    });

    dailyIngestionRule.addTarget(new targets.LambdaFunction(ingestionFunction));

    const restApi = new apigateway.RestApi(this, 'MoversRestApi', {
      restApiName: `${projectName}-api`,
      description: 'REST API for retrieving recent daily stock movers',
      cloudWatchRole: true,
      deployOptions: {
        stageName: 'prod',
        metricsEnabled: true,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: ['GET', 'OPTIONS'],
        allowHeaders: ['Content-Type'],
      },
    });

    const moversResource = restApi.root.addResource('movers');
    moversResource.addMethod('GET', new apigateway.LambdaIntegration(apiFunction));

    const frontendBucket = new s3.Bucket(this, 'FrontendBucket', {
      bucketName: `${projectName}-${this.account}-${this.region}`,
      websiteIndexDocument: 'index.html',
      websiteErrorDocument: 'index.html',
      publicReadAccess: true,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: true,
        ignorePublicAcls: true,
        blockPublicPolicy: false,
        restrictPublicBuckets: false,
      }),
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    new s3deploy.BucketDeployment(this, 'FrontendDeployment', {
      sources: [s3deploy.Source.asset(frontendDistPath)],
      destinationBucket: frontendBucket,
    });

    const alertTopic = new sns.Topic(this, 'AlertTopic', {
      topicName: `${projectName}-alerts`,
      displayName: 'Serverless Stock Dashboard Alerts',
    });

    const alertEmail = process.env.ALERT_EMAIL;

    if (alertEmail) {
      alertTopic.addSubscription(new subscriptions.EmailSubscription(alertEmail));
    }

    const ingestionErrorsAlarm = new cloudwatch.Alarm(this, 'IngestionErrorsAlarm', {
      alarmName: `${projectName}-ingestion-errors`,
      metric: ingestionFunction.metricErrors({ period: cdk.Duration.minutes(5) }),
      threshold: 1,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
    });

    ingestionErrorsAlarm.addAlarmAction(new cloudwatchActions.SnsAction(alertTopic));

    const apiErrorsAlarm = new cloudwatch.Alarm(this, 'ApiErrorsAlarm', {
      alarmName: `${projectName}-api-errors`,
      metric: apiFunction.metricErrors({ period: cdk.Duration.minutes(5) }),
      threshold: 1,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
    });

    apiErrorsAlarm.addAlarmAction(new cloudwatchActions.SnsAction(alertTopic));

    const apiGateway5xxAlarm = new cloudwatch.Alarm(this, 'ApiGateway5xxAlarm', {
      alarmName: `${projectName}-api-gateway-5xx`,
      metric: restApi.metricServerError({
        period: cdk.Duration.minutes(5),
      }),
      threshold: 1,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
    });

    apiGateway5xxAlarm.addAlarmAction(new cloudwatchActions.SnsAction(alertTopic));

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: `${restApi.url}movers`,
      description: 'GET /movers endpoint',
    });

    new cdk.CfnOutput(this, 'FrontendUrl', {
      value: frontendBucket.bucketWebsiteUrl,
      description: 'Public S3 static website URL',
    });

    new cdk.CfnOutput(this, 'TableName', {
      value: moversTable.tableName,
      description: 'DynamoDB table name',
    });

    new cdk.CfnOutput(this, 'SecretName', {
      value: stockApiSecretName,
      description: 'Secrets Manager secret name for the stock API key',
    });

    new cdk.CfnOutput(this, 'AlertTopicArn', {
      value: alertTopic.topicArn,
      description: 'SNS topic used by CloudWatch alarms',
    });
  }
}