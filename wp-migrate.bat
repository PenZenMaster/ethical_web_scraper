@echo off
REM WordPress Migration Tool - Quick Setup
REM Usage: wp-migrate.bat [urls_file] [output_name]

if "%1"=="" (
    echo WordPress Migration Tool
    echo.
    echo Usage: wp-migrate.bat [urls_file] [output_name]
    echo.
    echo Examples:
    echo   wp-migrate.bat wordpress_urls.txt my_site_import
    echo   wp-migrate.bat blog_posts.txt blog_migration
    echo.
    echo Files needed:
    echo   - URLs file with one WordPress URL per line
    echo   - config/wordpress.yaml ^(automatically used^)
    echo.
    echo Output: [output_name].xml ready for WordPress import
    goto end
)

set URLS_FILE=%1
set OUTPUT_NAME=%2

if "%OUTPUT_NAME%"=="" (
    set OUTPUT_NAME=wordpress_import
)

echo Starting WordPress migration...
echo URLs file: %URLS_FILE%
echo Output: %OUTPUT_NAME%.xml
echo.

REM Run the WordPress migration
".venv\Scripts\python.exe" main.py wordpress "%URLS_FILE%" --output "%OUTPUT_NAME%" --verbose

if %ERRORLEVEL% == 0 (
    echo.
    echo ========================================
    echo WordPress migration completed successfully!
    echo.
    echo Next steps:
    echo 1. Go to your WordPress Admin dashboard
    echo 2. Navigate to Tools ^> Import ^> WordPress
    echo 3. Upload: %OUTPUT_NAME%.xml
    echo 4. Review and import the content
    echo ========================================
) else (
    echo.
    echo Migration failed. Check the output above for errors.
)

:end