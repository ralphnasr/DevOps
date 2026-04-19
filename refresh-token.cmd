@echo off
REM ── ShopCloud Admin — Refresh Cognito JWT (every ~1 hour) ──
REM Run from repo root:  refresh-token.cmd
REM Then copy token.txt content and paste into ModHeader after "Bearer "

echo.
echo Requesting fresh admin JWT from Cognito...
aws cognito-idp initiate-auth ^
  --client-id 53cijv1al3rcj4vr6a9p0v8od2 ^
  --auth-flow USER_PASSWORD_AUTH ^
  --auth-parameters USERNAME=sarmad.farhat2017@gmail.com,PASSWORD=eece503Qproject ^
  --query "AuthenticationResult.IdToken" ^
  --output text > token.txt

if %ERRORLEVEL% neq 0 (
  echo.
  echo ERROR: Failed to get token. Check AWS credentials and Cognito user.
  pause
  exit /b 1
)

echo Token written to token.txt
echo Opening file — Ctrl+A, Ctrl+C, then paste into ModHeader after "Bearer "
echo.
notepad token.txt
