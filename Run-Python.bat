@echo off

:: PowerShell স্ক্রিপ্ট চালানো
powershell -ExecutionPolicy Bypass -File "C:\Users\tahch\Downloads\Documents\VS_Code\AmarDesh\vscode_hotkey.ps1"

:: 10 মিনিট পর শাটডাউন হবে
timeout /t 600

:: পপ-আপ মেসেজ দেখানো
msg * "To cancel the shutdown, close this command prompt window."

:: 60 সেকেন্ড অপেক্ষা করা
timeout /t 60

:: যদি command prompt বন্ধ না করা হয়, তাহলে শাটডাউন হবে
shutdown /s /f /t 0
