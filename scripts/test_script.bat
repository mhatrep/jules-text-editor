@echo off
echo Hello from Batch!
echo Arguments: %*
for /L %%i in (1,1,5) do (
    echo Batch count: %%i
    timeout /T 1 /NOBREAK > nul
)
echo Batch script finished. 1>&2
