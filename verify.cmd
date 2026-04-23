@echo off
REM ── ShopCloud end-to-end verification (Phase 1 infra + Phase 2 code) ──
REM Run from repo root:  verify.cmd

setlocal EnableDelayedExpansion
set REGION=us-east-1
set ACCOUNT=519718528172
set CLUSTER=shopcloud-prod
set CF=https://d3w3kfhcnfq6gy.cloudfront.net
set ALB=sc-prod-alb-1798766792.us-east-1.elb.amazonaws.com

echo.
echo ========================================
echo  PHASE 1 — Infrastructure verification
echo ========================================

echo.
echo [01] AWS identity
aws sts get-caller-identity --query "{Account:Account,Arn:Arn}" --output table

echo.
echo [02] VPCs (prod + dev)
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=shopcloud-*" --query "Vpcs[].{Name:Tags[?Key=='Name']|[0].Value,CIDR:CidrBlock,State:State}" --output table

echo.
echo [03] Subnets per VPC (expect public/private-app/private-data x 2 AZs each)
aws ec2 describe-subnets --filters "Name=tag:Name,Values=shopcloud-*" --query "Subnets[].{Name:Tags[?Key=='Name']|[0].Value,AZ:AvailabilityZone,CIDR:CidrBlock}" --output table

echo.
echo [04] NAT gateways
aws ec2 describe-nat-gateways --filter "Name=state,Values=available" --query "NatGateways[].{Id:NatGatewayId,VPC:VpcId,IP:NatGatewayAddresses[0].PublicIp}" --output table

echo.
echo [05] Security groups
aws ec2 describe-security-groups --filters "Name=group-name,Values=shopcloud-*" --query "SecurityGroups[].{Name:GroupName,VPC:VpcId}" --output table

echo.
echo [06] ECR repositories (5 expected: catalog/cart/checkout/admin/migrate)
aws ecr describe-repositories --query "repositories[?starts_with(repositoryName, 'shopcloud/')].{Name:repositoryName,URI:repositoryUri}" --output table

echo.
echo [07] Latest image per repo
for %%R in (catalog cart checkout admin migrate) do (
  echo   shopcloud/%%R:
  aws ecr describe-images --repository-name shopcloud/%%R --query "sort_by(imageDetails,&imagePushedAt)[-1].{Tags:imageTags,Pushed:imagePushedAt,SizeMB:imageSizeInBytes}" --output table
)

echo.
echo [08] RDS PostgreSQL
aws rds describe-db-instances --db-instance-identifier shopcloud-prod --query "DBInstances[0].{Status:DBInstanceStatus,Engine:Engine,Version:EngineVersion,Endpoint:Endpoint.Address,MultiAZ:MultiAZ,Encrypted:StorageEncrypted}" --output table

echo.
echo [09] ElastiCache Redis
aws elasticache describe-cache-clusters --show-cache-node-info --query "CacheClusters[?contains(CacheClusterId,'shopcloud')].{Id:CacheClusterId,Status:CacheClusterStatus,Engine:Engine,Node:CacheNodeType,Endpoint:CacheNodes[0].Endpoint.Address}" --output table

echo.
echo [10] ALB
aws elbv2 describe-load-balancers --query "LoadBalancers[?starts_with(LoadBalancerName,'sc-')].{Name:LoadBalancerName,DNS:DNSName,State:State.Code,Type:Type,Scheme:Scheme}" --output table

echo.
echo [11] Target group health (each TG individually)
aws elbv2 describe-target-groups --query "TargetGroups[?starts_with(TargetGroupName,'sc-')].TargetGroupArn" --output text > tgs.txt
for /f "tokens=1,2,3,4,5,6,7,8 delims=	 " %%A in (tgs.txt) do (
  for %%G in (%%A %%B %%C %%D %%E %%F %%G %%H) do (
    if not "%%G"=="" (
      echo   --- TG: %%G ---
      aws elbv2 describe-target-health --target-group-arn %%G --query "TargetHealthDescriptions[].{Id:Target.Id,Port:Target.Port,Health:TargetHealth.State}" --output table
    )
  )
)
del tgs.txt

echo.
echo [12] ECS cluster
aws ecs describe-clusters --clusters %CLUSTER% --query "clusters[0].{Name:clusterName,Status:status,Active:activeServicesCount,Running:runningTasksCount}" --output table

echo.
echo [13] ECS services (4 expected, all 1/1)
aws ecs describe-services --cluster %CLUSTER% --services catalog cart checkout admin --query "services[].{Name:serviceName,Status:status,Desired:desiredCount,Running:runningCount,Pending:pendingCount,TaskDef:taskDefinition}" --output table

echo.
echo [14] ECS deployments steady-state
aws ecs describe-services --cluster %CLUSTER% --services catalog cart checkout admin --query "services[].{Name:serviceName,Deployments:length(deployments),RolloutState:deployments[0].rolloutState}" --output table

echo.
echo [15] SSM parameters (DB/Redis/SQS/S3/Cognito)
aws ssm describe-parameters --query "Parameters[?starts_with(Name,'/prod/')].{Name:Name,Type:Type}" --output table

echo.
echo [16] Cognito user pools
aws cognito-idp list-user-pools --max-results 20 --query "UserPools[?starts_with(Name,'shopcloud')].{Id:Id,Name:Name}" --output table

echo.
echo [17] SQS queues
aws sqs list-queues --queue-name-prefix shopcloud --output table

echo.
echo [18] S3 buckets
aws s3api list-buckets --query "Buckets[?starts_with(Name,'shopcloud')].{Name:Name,Created:CreationDate}" --output table

echo.
echo [19] CloudFront distribution
aws cloudfront list-distributions --query "DistributionList.Items[].{Id:Id,Domain:DomainName,Status:Status,Enabled:Enabled,Origin:Origins.Items[0].DomainName}" --output table

echo.
echo [20] Bastion EC2
aws ec2 describe-instances --filters "Name=tag:Name,Values=shopcloud-*bastion*" "Name=instance-state-name,Values=running" --query "Reservations[].Instances[].{Id:InstanceId,IP:PublicIpAddress,State:State.Name,Type:InstanceType}" --output table

echo.
echo [21] SES sender identity
aws ses list-identities --query "Identities" --output table

echo.
echo [22] CloudWatch log groups
aws logs describe-log-groups --log-group-name-prefix /ecs/shopcloud --query "logGroups[].{Name:logGroupName,Retention:retentionInDays,SizeKB:storedBytes}" --output table

echo.
echo ========================================
echo  PHASE 2 — Application verification
echo ========================================

echo.
echo [23] CloudFront serves homepage
curl.exe -sS -o NUL -w "Status: %%{http_code}  Size: %%{size_download} bytes\n" %CF%/

echo.
echo [24] Catalog: list products
curl.exe -sS "%CF%/api/products?per_page=3" | findstr /C:"total"

echo.
echo [25] Catalog: categories
curl.exe -sS "%CF%/api/products/categories"
echo.

echo.
echo [26] Catalog: search
curl.exe -sS "%CF%/api/products/search?q=headphones&per_page=2" | findstr /C:"total"

echo.
echo [27] Catalog: best-sellers
curl.exe -sS "%CF%/api/products/best-sellers" | findstr /C:"name"

echo.
echo [28] Catalog: new-arrivals
curl.exe -sS "%CF%/api/products/new-arrivals" | findstr /C:"name"

echo.
echo [29] Catalog: product detail (id=1)
curl.exe -sS "%CF%/api/products/1" | findstr /C:"name"

echo.
echo [30] Catalog: related products
curl.exe -sS "%CF%/api/products/1/related"
echo.

echo.
echo [31] Catalog: reviews summary
curl.exe -sS "%CF%/api/products/1/reviews"
echo.

echo.
echo [32] Cart: requires auth (expect 401)
curl.exe -sS -o NUL -w "Status: %%{http_code}\n" "%CF%/api/cart"

echo.
echo [33] Checkout: orders requires auth (expect 401)
curl.exe -sS -o NUL -w "Status: %%{http_code}\n" "%CF%/api/orders"

echo.
echo [34] Admin service requires auth (expect 401/403)
curl.exe -sS -o NUL -w "Status: %%{http_code}\n" "%CF%/admin"

echo.
echo [35] Cognito Hosted UI reachable
pushd terraform
for /f "tokens=*" %%D in ('terraform output -raw cognito_customer_domain 2^>NUL') do set COG=%%D
popd
echo   Customer domain: !COG!
curl.exe -sS -o NUL -w "Status: %%{http_code}\n" "!COG!/login?response_type=code&client_id=test&redirect_uri=https://example.com"

echo.
echo [36] Direct ALB still healthy (bypasses CloudFront cache)
curl.exe -sS -o NUL -w "Status: %%{http_code}\n" "http://%ALB%/api/products?per_page=1"

echo.
echo [37] Database row counts (via ECS one-off task)
echo   Skipping — run app/scripts/check_db.py via ECS task only if needed.

echo.
echo ========================================
echo  Verification complete.
echo  Open in browser: %CF%
echo ========================================
endlocal
