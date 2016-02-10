% bugme

Windows Notification Icon and Messages

Bugme!
======

This program is intended to demonstrate robust usage of the Win32
`Shell_NotifyIcon()` interface for adding system tray icons, and then
producing "balloon" notifications.  The MSDN documentation borders on
useless, and most search results provide terse and un-documented code samples
that don't help in understanding the API.

The end result, however, is a general-purpose command-line tool that can
quickly and easily display a notification message to the user.  The tool is a
vastly simplified version of the `notify-send` command that many users of X
desktops use to display notifications.  The biggest difference is that the
Win32 API doesn't give you a lot of freedom in customizing the notification
(which is fine for 99% of my use cases).

Building
========

This program produces a native Windows program using MinGW.  It does not rely
on Cygwin once built, but the build environment does.  I plan to add a Visual
Studio solution in the future.

To build this under Cygwin, make sure you have 64-bit MinGW and GNU make
installed.  Then, the following should work:

    make

Installing
==========

Install into your prefix (`/usr/local` by default) with the following:

    make install

Otherwise, copy the file from `build/bugme.exe` to anywhere in your path.

Usage
=====

    bugme.exe [message [title]]

Without any arguments, the message is "You've been bugged!", and the title is
"Bugme!".  The first argument will replace the default message with a string
of your choice (up to 255 characters).  The second argument will replace the
default title with a string of your choice (up to 63 characters).

