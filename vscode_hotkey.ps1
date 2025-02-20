Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Keyboard {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern void keybd_event(byte bVk, byte bScan, int dwFlags, int dwExtraInfo);
}
"@ -Language CSharp

# VS Code চালু করার 10 সেকেন্ড আগে Windows কী চাপা হবে
Start-Sleep -Seconds 10
[Keyboard]::keybd_event(0x5B, 0, 0, 0)  # Win চাপা
Start-Sleep -Milliseconds 100
[Keyboard]::keybd_event(0x5B, 0, 2, 0)  # Win ছাড়া

# VS Code চালু করা
Start-Process "C:\Users\tahch\AppData\Local\Programs\Microsoft VS Code\Code.exe"

# VS Code চালু হওয়ার জন্য 20 সেকেন্ড অপেক্ষা করা
Start-Sleep -Seconds 30

# কীবোর্ড শর্টকাট প্রেস করা (Ctrl + Win + X)
[Keyboard]::keybd_event(0x11, 0, 0, 0)  # Ctrl চাপা
[Keyboard]::keybd_event(0x5B, 0, 0, 0)  # Win চাপা
[Keyboard]::keybd_event(0x58, 0, 0, 0)  # X চাপা
Start-Sleep -Milliseconds 100
[Keyboard]::keybd_event(0x58, 0, 2, 0)  # X ছাড়া
[Keyboard]::keybd_event(0x5B, 0, 2, 0)  # Win ছাড়া
[Keyboard]::keybd_event(0x11, 0, 2, 0)  # Ctrl ছাড়া
