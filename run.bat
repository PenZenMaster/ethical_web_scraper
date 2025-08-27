@echo off
REM Ethical Web Scraper - Virtual Environment Runner
REM Usage: run.bat [command] [options]
REM Example: run.bat scrape "https://example.com" --selector "h1"

if "%1"=="" (
    echo Ethical Web Scraper - Production-Ready Content Migration Tool
    echo.
    echo Usage: run.bat [command] [options]
    echo.
    echo Commands:
    echo   run.bat --help                           Show main help
    echo   run.bat scrape "url" --selector "div"    Extract specific content
    echo   run.bat batch urls.txt --format csv      Process multiple URLs
    echo   run.bat wordpress urls.txt --output wp   WordPress migration
    echo   run.bat test                             Test functionality
    echo.
    echo WordPress Migration:
    echo   wp-migrate.bat urls.txt migration_name   Quick WordPress import
    echo.
    echo Get command-specific help:
    echo   run.bat [command] --help
    echo.
    goto end
)

REM Run the command with virtual environment Python
".venv\Scripts\python.exe" main.py %*

:end