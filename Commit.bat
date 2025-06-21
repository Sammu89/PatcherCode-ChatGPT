@echo off
setlocal enabledelayedexpansion

REM Go to the folder where this script is located
cd /d "%~dp0"

REM Check if Git is configured
git config --global user.email >nul 2>&1
if errorlevel 1 (
    echo Configuring Git for the first time...
    git config --global user.email "samuel.leca@gmail.com"
    git config --global user.name "Sammu89"
    echo Git configured successfully!
    echo.
) else (
    REM Check if it already has the correct configurations
    for /f "delims=" %%i in ('git config --global user.email') do set current_email=%%i
    for /f "delims=" %%i in ('git config --global user.name') do set current_name=%%i
    
    if not "!current_email!"=="samuel.leca@gmail.com" (
        echo Updating email configuration...
        git config --global user.email "samuel.leca@gmail.com"
    )
    
    if not "!current_name!"=="Sammu89" (
        echo Updating name configuration...
        git config --global user.name "Sammu89"
    )
)

REM Check if it's already a Git repository
echo Checking if this is a Git repository...
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo This folder is not a Git repository.
    echo.
    set /p create_repo="Do you want to create a new repository? (y/n): "
    
    if /i "!create_repo!"=="y" (
        goto create_new_repo
    ) else (
        echo Operation cancelled.
        pause
        exit /b 0
    )
) else (
    echo This is already a Git repository.
    goto check_remote
)

:create_new_repo
        echo.
        set /p repo_name="Repository name (no spaces): "
        
        if "!repo_name!"=="" (
            echo Invalid name. Exiting...
            pause
            exit /b 1
        )
        
        echo.
        echo Creating local Git repository...
        git init
        
        echo.
        echo Choose the remote repository type:
        echo 1. GitHub
        echo 2. GitLab
        echo 3. Other (manual)
        set /p repo_type="Choose (1-3): "
        
        if "!repo_type!"=="1" (
            set remote_url=https://github.com/Sammu89/!repo_name!.git
            echo.
            echo WARNING: You need to create the repository on GitHub first!
            echo URL: https://github.com/new
            echo Repository name: !repo_name!
            echo.
            set /p continue="Have you already created the repository on GitHub? (y/n): "
            if /i not "!continue!"=="y" (
                echo Create the repository on GitHub first and run again.
                pause
                exit /b 1
            )
        ) else if "!repo_type!"=="2" (
            set remote_url=https://gitlab.com/Sammu89/!repo_name!.git
            echo.
            echo WARNING: You need to create the repository on GitLab first!
            echo URL: https://gitlab.com/projects/new
            echo Repository name: !repo_name!
            echo.
            set /p continue="Have you already created the repository on GitLab? (y/n): "
            if /i not "!continue!"=="y" (
                echo Create the repository on GitLab first and run again.
                pause
                exit /b 1
            )
        ) else if "!repo_type!"=="3" (
            echo.
            set /p remote_url="Remote repository URL: "
            if "!remote_url!"=="" (
                echo Invalid URL. Exiting...
                pause
                exit /b 1
            )
        ) else (
            echo Invalid option. Exiting...
            pause
            exit /b 1
        )
        
        echo.
        echo Adding remote origin...
        git remote add origin !remote_url!
        
        REM Create README if it doesn't exist
        if not exist "README.md" (
            echo # !repo_name! > README.md
            echo. >> README.md
            echo Repository created automatically. >> README.md
        )
        
        REM Create .gitignore
        echo.
        echo Creating .gitignore file...
        
        REM Basic gitignore
        echo # System files > .gitignore
        echo .DS_Store >> .gitignore
        echo Thumbs.db >> .gitignore
        echo desktop.ini >> .gitignore
        echo. >> .gitignore
        echo # Temporary files >> .gitignore
        echo *.tmp >> .gitignore
        echo *.temp >> .gitignore
        echo *.log >> .gitignore
        echo. >> .gitignore
        echo # Python >> .gitignore
        echo __pycache__/ >> .gitignore
        echo *.pyc >> .gitignore
        echo *.pyo >> .gitignore
        echo. >> .gitignore
        echo # Dependency folders >> .gitignore
        echo node_modules/ >> .gitignore
        echo vendor/ >> .gitignore
        echo. >> .gitignore
        
        echo Basic .gitignore created!
        echo.
        set /p add_custom="Do you want to add custom folders/files to .gitignore? (y/n): "
        
        if /i "!add_custom!"=="y" (
            echo.
            echo ==============================================
            echo   .GITIGNORE CUSTOMIZATION
            echo ==============================================
            echo.
            echo INSTRUCTIONS:
            echo - To ignore file: filename.txt
            echo - To ignore extension: *.pdf
            echo - To ignore folder: foldername/
            echo - To ignore everything in folder: folder/*
            echo - Empty line to finish
            echo.
            
            :add_gitignore_loop
            set /p ignore_item="Add item (or ENTER to finish): "
            
            if "!ignore_item!"=="" (
                goto end_gitignore
            )
            
            echo !ignore_item! >> .gitignore
            echo Added: !ignore_item!
            goto add_gitignore_loop
            
            :end_gitignore
            echo.
            echo Custom .gitignore created!
            echo.
            echo Final .gitignore content:
            echo ==========================================
            type .gitignore
            echo ==========================================
        )
        
        echo.
        echo Repository configured successfully!
        echo Remote: !remote_url!
        echo.
        goto check_remote
    ) else (
        echo Operation cancelled.
        pause
        exit /b 0
    )
)

:check_remote

REM Check if there's a remote configured
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo.
    echo No remote repository configured.
    set /p add_remote="Do you want to add a remote repository? (y/n): "
    
    if /i "!add_remote!"=="y" (
        echo.
        set /p remote_url="Remote repository URL: "
        if not "!remote_url!"=="" (
            git remote add origin !remote_url!
            echo Remote added successfully!
        )
    )
)

REM Add everything (including if you've modified .gitignore)
echo.
echo Adding files...
git add .

REM Debug: Show status
echo.
echo Git status:
git status --porcelain

REM Check if there are any changes at all (staged or unstaged)
git diff --quiet && git diff --cached --quiet
if not errorlevel 1 (
    echo.
    echo ================================
    echo   No changes detected.
    echo   Repository is up to date!
    echo ================================
    echo.
    echo Debug info:
    echo Current branch: 
    git branch --show-current
    echo.
    echo Remote status:
    git remote -v
    echo.
    echo Last commit:
    git log --oneline -1
    pause
    exit /b 0
)

REM Check if there's something to commit (this should now always pass)
git diff --staged --quiet
if not errorlevel 1 (
    echo.
    echo ================================
    echo   No changes staged for commit.
    echo   Repository is up to date!
    echo ================================
    pause
    exit /b 0
)

REM Generate comment with date and time
for /f "tokens=1-5 delims=/ " %%a in ("%date% %time%") do (
    set commitmsg=Automatic commit - %%a-%%b-%%c at %%d:%%e
)

REM Make commit
echo Making commit...
git commit -m "!commitmsg!"
if errorlevel 1 (
    echo Commit error.
    pause
    exit /b 1
)

REM Check if it's the first push and get current branch name
for /f "delims=" %%i in ('git branch --show-current') do set current_branch=%%i

REM If no current branch name (old Git versions), default to master
if "!current_branch!"=="" (
    for /f "tokens=2" %%i in ('git branch') do set current_branch=%%i
)

REM Try to check if remote branch exists
git rev-parse --verify origin/!current_branch! >nul 2>&1
if errorlevel 1 (
    echo.
    echo Making first push to !current_branch! branch...
    git push -u origin !current_branch!
) else (
    echo.
    echo Pushing to !current_branch! branch...
    git push origin !current_branch!
)

if errorlevel 1 (
    echo.
    echo Push error. Possible causes:
    echo - Remote repository doesn't exist
    echo - Authentication problems
    echo - No internet connection
    echo.
    echo For authentication:
    echo - HTTPS: use personal token instead of password
    echo - SSH: configure SSH key
    pause
    exit /b 1
)

echo.
echo ================================
echo   Commit completed successfully!
echo ================================
pause