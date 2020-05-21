FOR /F "usebackq" %%a IN (`where pip.exe`) DO (
 set pip_dir=%%a
)
%pip_dir% install -r req.txt --index-url https://pypi.org/pypi/simple --trusted-host pypi.org --user 