#!/cygdrive/c/Python35/python.exe
#=============================================================================
#
# Example Win32 Notification API Usage
#
#=============================================================================

"""
Example Win32 Notification API Usage
====================================
"""


import ctypes
import ctypes.wintypes
import logging
import os
import sys
import time
import uuid


__version__ = '0.0.0'


# Set logging level.
logging.basicConfig( level = logging.WARN )


#-----------------------------------------------------------------------------
# Define additional types needed for the Win32 API.
#-----------------------------------------------------------------------------

ctypes.wintypes.HCURSOR = ctypes.wintypes.HANDLE
ctypes.wintypes.TCHAR   = ctypes.c_char
ctypes.wintypes.LPCTSTR = ctypes.c_char_p
ctypes.wintypes.LPTSTR  = ctypes.wintypes.LPCTSTR
ctypes.wintypes.LRESULT = ctypes.c_long
ctypes.wintypes.va_list = ctypes.c_char_p


#-----------------------------------------------------------------------------
# Callback function type needed for certain structures.
#-----------------------------------------------------------------------------

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.wintypes.HWND,
    ctypes.c_uint,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM
)


#-----------------------------------------------------------------------------
# Structures and objects needed for the notification API.
#-----------------------------------------------------------------------------

#=============================================================================
class GUID( ctypes.Structure ):
    """
    Win32 GUID ctypes Structure

    UUID strings are five, dash-separated sequences of hexadecimal digits:

        9B96F0A9-51AD-4031-9306-DEAA0272603F

    The first sequence is the Data1 field (32-bit integer).
    The second sequence is the Data2 field (16-bit integer).
    The third sequence is the Data3 field (16-bit integer).
    The fourth sequence is the first two bytes of the Data4 field.
    The fifth sequence is the remaining six bytes of the Data4 field.

    typedef struct _GUID {
        DWORD Data1;
        WORD  Data2;
        WORD  Data3;
        BYTE  Data4[8];
    } GUID;
    """

    # Array sizes
    DATA4_SIZE = 8

    # Internal array types
    GUID_DATA4_TYPE = ctypes.wintypes.BYTE * DATA4_SIZE

    # Structure layout
    _fields_ = [
        ( 'Data1', ctypes.wintypes.DWORD ),
        ( 'Data2', ctypes.wintypes.WORD  ),
        ( 'Data3', ctypes.wintypes.WORD  ),
        ( 'Data4', GUID_DATA4_TYPE       )
    ]


    #=========================================================================
    def __init__( self, string = None, *args, **kwargs ):
        """
        GUID structure initializer.

        @param string Optionally specify initial data as a UUID string.
        """
        if type( string ) is str:
            super().__init__( *args, **kwargs )
            self.load_from_string( string )
        else:
            my_args = args.insert( 0, string )
            super().__init__( *args, **kwargs )


    #=========================================================================
    def __str__( self ):
        """
        Converts the GUID to its string representation.

        @return The dashed string representation of the GUID.
        """
        node = 0
        for dindex, shift in zip( range( 2, 8 ), range( 40, -1, -8 ) ):
            node |= ( self.Data4[ dindex ] & 0xFF ) << shift
        repr_id = uuid.UUID(
            fields = (
                self.Data1,
                self.Data2,
                self.Data3,
                self.Data4[ 0 ] & 0xFF,
                self.Data4[ 1 ] & 0xFF,
                node
            )
        )
        return repr_id.urn.split( ':' )[ 2 ].upper()


    #=========================================================================
    def load_from_string( self, string ):
        """
        Loads a GUID from a string.

        @param string URN string representing the UUID
        """

        # Use uuid module to parse string, and load into integers.
        load_id    = uuid.UUID( string )

        # Place integer fields into structure members.
        self.Data1 = load_id.fields[ 0 ]
        self.Data2 = load_id.fields[ 1 ]
        self.Data3 = load_id.fields[ 2 ]

        # The `Data4` field is composed of the last three UUID fields.
        self.Data4 = self.GUID_DATA4_TYPE()

        # Use the clock_seq_hi_variant for the first `Data4` byte.
        self.Data4[ 0 ] = load_id.fields[ 3 ]

        # Use the clock_seq_low for the second `Data4` byte.
        self.Data4[ 1 ] = load_id.fields[ 4 ]

        # Use the node field for the remaining six `Data4` bytes.
        node = load_id.fields[ 5 ]
        for dindex, shift in zip( range( 2, 8 ), range( 40, -1, -8 ) ):
            self.Data4[ dindex ] = ( node >> shift ) & 0xFF


    #=========================================================================
    def _self_test( self ):
        """
        Self-test sanity check.
        """
        generated = uuid.uuid4()
        expected  = str( generated ).upper()
        self.load_from_string( expected )
        actual = str( self )
        if expected != actual:
            return False
        return True


#=============================================================================
class NID_ANON_UNION( ctypes.Union ):
    _fields_ = [
        ( 'uTimeout', ctypes.wintypes.UINT ),
        ( 'uVersion', ctypes.wintypes.UINT )
    ]


#=============================================================================
class NOTIFYICONDATA( ctypes.Structure ):
    """
    Win32 NOTIFYICONDATA ctype Structure

    Note: MSDN docs state szTip is 64, headers show 128.
    Note: hBalloonIcon requires Windows 7 and later (setting NTTDI_VERSION).

    typedef struct _NOTIFYICONDATA {
        DWORD cbSize;
        HWND  hWnd;
        UINT  uID;
        UINT  uFlags;
        UINT  uCallbackMessage;
        HICON hIcon;
        TCHAR szTip[64];
        DWORD dwState;
        DWORD dwStateMask;
        TCHAR szInfo[256];
        union {
            UINT uTimeout;
            UINT uVersion;
        };
        TCHAR szInfoTitle[64];
        DWORD dwInfoFlags;
        GUID  guidItem;
        HICON hBalloonIcon;
    } NOTIFYICONDATA, *PNOTIFYICONDATA;
    """

    # Array sizes
    TIP_SIZE   = 128
    INFO_SIZE  = 256
    TITLE_SIZE = 64

    # Unnamed members
    _anonymous_ = ( '_anon_union', )

    # Structure layout
    _fields_ = [
        ( 'cbSize',           ctypes.wintypes.DWORD              ),
        ( 'hWnd',             ctypes.wintypes.HWND               ),
        ( 'uID',              ctypes.wintypes.UINT               ),
        ( 'uFlags',           ctypes.wintypes.UINT               ),
        ( 'uCallbackMessage', ctypes.wintypes.UINT               ),
        ( 'hIcon',            ctypes.wintypes.HICON              ),
        ( 'szTip',            ctypes.wintypes.TCHAR * TIP_SIZE   ),
        ( 'dwState',          ctypes.wintypes.DWORD              ),
        ( 'dwStateMask',      ctypes.wintypes.DWORD              ),
        ( 'szInfo',           ctypes.wintypes.TCHAR * INFO_SIZE  ),
        ( '_anon_union',      NID_ANON_UNION                     ),
        ( 'szInfoTitle',      ctypes.wintypes.TCHAR * TITLE_SIZE ),
        ( 'dwInfoFlags',      ctypes.wintypes.DWORD              ),
        ( 'guidItem',         GUID                               )
    ]


#=============================================================================
class WINDCLASS( ctypes.Structure ):
    """
    typedef struct tagWNDCLASS {
        UINT      style;
        WNDPROC   lpfnWndProc;
        int       cbClsExtra;
        int       cbWndExtra;
        HINSTANCE hInstance;
        HICON     hIcon;
        HCURSOR   hCursor;
        HBRUSH    hbrBackground;
        LPCTSTR   lpszMenuName;
        LPCTSTR   lpszClassName;
    } WNDCLASS, *PWNDCLASS;
    """
    _fields_ = [
        ( 'style',         ctypes.wintypes.UINT ),
        ( 'lpfnWndProc',   WNDPROC ),
        ( 'cbClsExtra',    ctypes.c_int ),
        ( 'cbWndExtra',    ctypes.c_int ),
        ( 'hInstance',     ctypes.wintypes.HINSTANCE ),
        ( 'hIcon',         ctypes.wintypes.HICON ),
        ( 'hCursor',       ctypes.wintypes.HCURSOR ),
        ( 'hbrBackground', ctypes.wintypes.HBRUSH ),
        ( 'lpszMenuName',  ctypes.wintypes.LPCSTR ),
        ( 'lpszClassName', ctypes.wintypes.LPCSTR )
    ]


#=============================================================================
class WNDCLASSEX( ctypes.Structure ):
    """
    typedef struct tagWNDCLASSEX {
        UINT      cbSize;
        UINT      style;
        WNDPROC   lpfnWndProc;
        int       cbClsExtra;
        int       cbWndExtra;
        HINSTANCE hInstance;
        HICON     hIcon;
        HCURSOR   hCursor;
        HBRUSH    hbrBackground;
        LPCTSTR   lpszMenuName;
        LPCTSTR   lpszClassName;
        HICON     hIconSm;
    } WNDCLASSEX, *PWNDCLASSEX;
    """
    _fields_ = [
        ( 'cbSize',        ctypes.wintypes.UINT ),
        ( 'style',         ctypes.wintypes.UINT ),
        ( 'lpfnWndProc',   WNDPROC ),
        ( 'cbClsExtra',    ctypes.c_int ),
        ( 'cbWndExtra',    ctypes.c_int ),
        ( 'hInstance',     ctypes.wintypes.HINSTANCE ),
        ( 'hIcon',         ctypes.wintypes.HICON ),
        ( 'hCursor',       ctypes.wintypes.HCURSOR ),
        ( 'hbrBackground', ctypes.wintypes.HBRUSH ),
        ( 'lpszMenuName',  ctypes.wintypes.LPCSTR ),
        ( 'lpszClassName', ctypes.wintypes.LPCSTR ),
        ( 'hIconSm',       ctypes.wintypes.HICON )
    ]


#-----------------------------------------------------------------------------
# Win32 API Constants
#-----------------------------------------------------------------------------

# CreateWindow default code
CW_USEDEFAULT = 0x80000000

# DWORD dwMessage
NIM_ADD        = 0
NIM_MODIFY     = 1
NIM_DELETE     = 2
NIM_SETFOCUS   = 3
NIM_SETVERSION = 4

# UINT uFlags
NIF_MESSAGE  = 0x00000001
NIF_ICON     = 0x00000002
NIF_TIP      = 0x00000004
NIF_STATE    = 0x00000008
NIF_INFO     = 0x00000010
NIF_GUID     = 0x00000020
NIF_REALTIME = 0x00000040
NIF_SHOWTIP  = 0x00000080

# DWORD dwInfoFlags
NIIF_NONE               = 0x00000000
NIIF_INFO               = 0x00000001
NIIF_WARNING            = 0x00000002
NIIF_ERROR              = 0x00000003
NIIF_USER               = 0x00000004
NIIF_NOSOUND            = 0x00000010
NIIF_LARGE_ICON         = 0x00000020
NIIF_RESPECT_QUIET_TIME = 0x00000080

# DWORD dwState/dwStateMask
NIS_HIDDEN     = 0x00000001
NIS_SHAREDICON = 0x00000002

# UINT uVersion
NOTIFYICON_VERSION_4 = 4

WM_DESTROY = 0x00000002
WM_USER    = 0x00000400

# Notification balloon events IDs
NIN_BALLOONSHOW      = WM_USER + 2
NIN_BALLOONHIDE      = WM_USER + 3
NIN_BALLOONTIMEOUT   = WM_USER + 4
NIN_BALLOONUSERCLICK = WM_USER + 5


#-----------------------------------------------------------------------------
# Win32 API Function Prototypes
#-----------------------------------------------------------------------------

#=============================================================================
ctypes.windll.user32.CreateWindowExA.argtypes = (
    ctypes.wintypes.DWORD,
    ctypes.wintypes.LPCTSTR,
    ctypes.wintypes.LPCTSTR,
    ctypes.wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.wintypes.HWND,
    ctypes.wintypes.HMENU,
    ctypes.wintypes.HINSTANCE,
    ctypes.wintypes.LPVOID
)
ctypes.windll.user32.CreateWindowExA.restype = ctypes.wintypes.HWND

#=============================================================================
ctypes.windll.user32.DefWindowProcA.argtypes = (
    ctypes.wintypes.HWND,
    ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM
)
ctypes.windll.user32.DefWindowProcA.restype = ctypes.wintypes.LRESULT

#=============================================================================
ctypes.windll.user32.DestroyWindow.argtypes = (
    ctypes.wintypes.HWND,
)
ctypes.windll.user32.DestroyWindow.restype = ctypes.wintypes.BOOL

#=============================================================================
ctypes.windll.user32.DispatchMessageA.argtypes = (
    ctypes.wintypes.LPMSG,
)
ctypes.windll.user32.DispatchMessageA.restype = ctypes.wintypes.LRESULT

#=============================================================================
ctypes.windll.kernel32.FormatMessageA.argtypes = (
    ctypes.wintypes.DWORD,
    ctypes.wintypes.LPCVOID,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.LPTSTR,
    ctypes.wintypes.DWORD,
    ctypes.POINTER( ctypes.wintypes.va_list )
)
ctypes.windll.kernel32.FormatMessageA.restype = ctypes.wintypes.DWORD

#=============================================================================
ctypes.windll.user32.GetMessageA.argtypes = (
    ctypes.wintypes.LPMSG,
    ctypes.wintypes.HWND,
    ctypes.wintypes.UINT,
    ctypes.wintypes.UINT
)
ctypes.windll.user32.GetMessageA.restype = ctypes.wintypes.BOOL

#=============================================================================
ctypes.windll.kernel32.GetModuleHandleA.argtypes = (
    ctypes.wintypes.LPCTSTR,
)
ctypes.windll.kernel32.GetModuleHandleA.restype = ctypes.wintypes.HMODULE

#=============================================================================
ctypes.windll.kernel32.GetLastError.argtypes = ()
ctypes.windll.kernel32.GetLastError.restype = ctypes.wintypes.DWORD

#=============================================================================
ctypes.windll.user32.LoadIconA.argtypes = (
    ctypes.wintypes.HINSTANCE,
    ctypes.wintypes.LPCTSTR
)
ctypes.windll.user32.LoadIconA.restype = ctypes.wintypes.HICON

#=============================================================================
ctypes.windll.user32.LoadImageA.argtypes = (
    ctypes.wintypes.HINSTANCE,
    ctypes.wintypes.LPCTSTR,
    ctypes.wintypes.UINT,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.wintypes.UINT
)
ctypes.windll.user32.LoadImageA.restype = ctypes.wintypes.HANDLE

#=============================================================================
ctypes.windll.user32.PostQuitMessage.argtypes = (
    ctypes.c_int,
)
ctypes.windll.user32.PostQuitMessage.restype = None

#=============================================================================
ctypes.windll.user32.RegisterClassExA.argtypes = (
    ctypes.POINTER( WNDCLASSEX ),
)
ctypes.windll.user32.RegisterClassExA.restype = ctypes.wintypes.ATOM

#=============================================================================
ctypes.windll.shell32.Shell_NotifyIconA.argtypes = (
    ctypes.wintypes.DWORD,
    ctypes.POINTER( NOTIFYICONDATA )
)
ctypes.windll.shell32.Shell_NotifyIconA.restype = ctypes.wintypes.BOOL

#=============================================================================
ctypes.windll.user32.UnregisterClassA.argtypes = (
    ctypes.wintypes.LPCTSTR,
    ctypes.wintypes.HINSTANCE
)
ctypes.windll.user32.UnregisterClassA.restype = ctypes.wintypes.BOOL

#=============================================================================
ctypes.windll.user32.UpdateWindow.argtypes = (
    ctypes.wintypes.HWND,
)
ctypes.windll.user32.UpdateWindow.restype = ctypes.wintypes.BOOL


#-----------------------------------------------------------------------------
# Application Constants
#-----------------------------------------------------------------------------

APPLICATION_MESSAGE_ID = WM_USER + 24
APPLICATION_NAME       = 'Bugme!'
WINDOW_CLASS_NAME      = 'bugme_class'

# Create a path to the icon shown in the tray.
script_path = os.path.realpath( __file__ )
script_dir  = os.path.dirname( script_path )
project_dir = os.path.dirname( script_dir )
icon_dir    = os.path.join( project_dir, 'icons' )
ICON_PATH   = os.path.join( icon_dir, 'bugme.ico' )


#-----------------------------------------------------------------------------
# Convenience Functions for the Application
#-----------------------------------------------------------------------------


#=============================================================================
def format_last_error():
    """
    Produces a string message of the last error that occurred.

    @return A string describing the most recent Win32 API error
    """

    # Error message buffer size.
    BUFFER_SIZE = 128

    # Message buffer.
    message = ctypes.create_string_buffer( BUFFER_SIZE )

    # Most recent error code.
    code = ctypes.windll.kernel32.GetLastError()

    # Convert error code to string.
    FORMAT_MESSAGE_FROM_HMODULE = 0x00000800
    FORMAT_MESSAGE_FROM_SYSTEM  = 0x00001000
    flags = FORMAT_MESSAGE_FROM_HMODULE | FORMAT_MESSAGE_FROM_SYSTEM
    result = ctypes.windll.kernel32.FormatMessageA(
        flags,                      # DWORD    dwFlags
        None,                       # LPCVOID  lpSource
        code,                       # DWORD    dwMessageId
        0,                          # DWORD    dwLanguageId
        ctypes.pointer( message ),  # LPTSTR   lpBufffer
        BUFFER_SIZE,                # DWORD    nSize
        None                        # va_list* Arguments
    )

    # Check success of formatting the error string.
    if result == 0:
        raise RuntimeError( 'FormatMessageW() failed.' )

    # Return the message as a string.
    return str( message )


#=============================================================================
def strarg( string ):
    """
    String-passing "macro" to convert Python (Unicode) strings into character
    strings suitable for passing to the ASCII Win32 interfaces.

    @param string The string for which to build an argument object
    """
    return ctypes.c_char_p( bytes( string, 'ascii' ) )


#=============================================================================
def notify_procedure( hWnd, uMsg, wParam, lParam ):
    """
    Handles messages for the window class.

    @param hWnd   Destination window handle
    @param uMsg   Event message ID
    @param wParam Context-specific additional parameter
    @param lParam Context-specific additional parameter
    """

    # Application message.
    if uMsg == APPLICATION_MESSAGE_ID:

        logging.debug( 'Application message received in window procedure.' )

        # Determine details of important events to handle.
        event = lParam & 0x0000FFFF;
        if     ( event == NIN_BALLOONTIMEOUT   ) \
            or ( event == NIN_BALLOONHIDE      ) \
            or ( event == NIN_BALLOONUSERCLICK ):

            # Free the window responsible for the tray item.
            ctypes.windll.user32.DestroyWindow( hWnd )

            # Unregister the window class.
            ctypes.windll.user32.UnregisterClassA(
                strarg( WINDOW_CLASS_NAME ),
                ctypes.windll.kernel32.GetModuleHandleA( None )
            )

    # Window destroy message.
    elif uMsg == WM_DESTROY:

        logging.debug( 'WM_DESTROY received in window procedure.' )

        # Prepare to remove the tray item.
        notify_data = NOTIFYICONDATA(
            cbSize = ctypes.sizeof( NOTIFYICONDATA ),
            hWnd   = hWnd
        )

        # Remove the tray item.
        result = ctypes.windll.shell32.Shell_NotifyIconA(
            NIM_DELETE,
            ctypes.byref( notify_data )
        )

        # Check romoval.
        if bool( result ) == False:
            raise RuntimeError( 'Unable to delete notification item.' )

        logging.debug( 'Notification item deleted.' )

        # Indicate the application is shutting down.
        ctypes.windll.user32.PostQuitMessage( 0 )

    # All other messages.
    else:

        # Pass message on to default handler.
        return ctypes.windll.user32.DefWindowProcA(
            hWnd,
            uMsg,
            wParam,
            lParam
        )

    # Indicate message was handled here.
    return 0


#=============================================================================
def notify( message, title = 'Bugme!' ):
    """
    Use the Win32 API to display a notification balloon.

    @param message The message contents to display
    @param title   The title of the message to display
    """

    # Get current program module handle.
    module_handle = ctypes.windll.kernel32.GetModuleHandleA( None )

    # Define the window class.
    window_class = WNDCLASSEX(
        cbSize        = ctypes.sizeof( WNDCLASSEX ),
        hInstance     = module_handle,
        lpszClassName = strarg( WINDOW_CLASS_NAME ),
        lpfnWndProc   = WNDPROC( notify_procedure )
    )

    # Register the window class.
    class_atom = ctypes.windll.user32.RegisterClassExA(
        ctypes.byref( window_class )
    )

    # Check class registration.
    if class_atom == 0:
        raise RuntimeError( 'Unable to register window class.' )

    logging.debug( 'Window class registered.' )

    # Set the window style flags.
    WS_OVERLAPPED = 0x00000000
    WS_SYSMENU    = 0x00080000
    style = WS_OVERLAPPED | WS_SYSMENU

    # Create the window that owns the notification.
    window_handle = ctypes.windll.user32.CreateWindowExA(
        0,                              # DWORD     dwExStyle
        strarg( WINDOW_CLASS_NAME ),    # LPCTSTR   lpClassName
        strarg( APPLICATION_NAME ),     # LPCTSTR   lpWindowName
        style,                          # DWORD     dwStyle
        0,                              # int       x
        0,                              # int       y
        CW_USEDEFAULT,                  # int       nWidth
        CW_USEDEFAULT,                  # int       nHeight
        0,                              # HWND      hWndParent
        0,                              # HMENU     hMenu
        module_handle,                  # HINSTANCE hInstance
        None                            # LPVOID    lpParam
    )

    # Check window creation.
    if bool( window_handle ) == False:
        raise RuntimeError( 'Unable to create window.' )
    logging.debug( 'Window created.' )

    # Load the icon into an icon instance.
    try:
        IMAGE_ICON      = 1
        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE  = 0x00000040
        icon_handle     = ctypes.windll.user32.LoadImageA(
            module_handle,
            strarg( ICON_PATH ),
            IMAGE_ICON,
            0,
            0,
            ( LR_LOADFROMFILE | LR_DEFAULTSIZE )
        )
    except:
        IDI_INFORMATION = 32516
        icon_handle     = ctypes.windll.user32.LoadIconA( 0, IDI_INFORMATION )

    # Check icon instance.
    if bool( icon_handle ) == False:
        raise RuntimeError( 'Unable to load icon.' )
    logging.debug( 'Icon loaded.' )

    # Set notification data field flags.
    nid_flags = NIF_ICON | NIF_MESSAGE | NIF_TIP

    # Define the notification data for the notification icon.
    notify_data = NOTIFYICONDATA(
        cbSize           = ctypes.sizeof( NOTIFYICONDATA ),
        hWnd             = window_handle,
        uFlags           = nid_flags,
        uCallbackMessage = APPLICATION_MESSAGE_ID,
        hIcon            = icon_handle,
        szTip            = bytes( APPLICATION_NAME, 'ascii' )
    )

    # Add the notification item to the tray.
    result = ctypes.windll.shell32.Shell_NotifyIconA(
        NIM_ADD,
        ctypes.byref( notify_data )
    )

    # Check notification item.
    if bool( result ) == False:
        raise RuntimeError( 'Unable to add notification icon.' )
    logging.debug( 'Notification item added.' )

    # Define the notification data to display a balloon message.
    notify_data = NOTIFYICONDATA(
        cbSize      = ctypes.sizeof( NOTIFYICONDATA ),
        hWnd        = window_handle,
        uFlags      = NIF_INFO,
        hIcon       = icon_handle,
        szInfo      = bytes( message, 'ascii' ),
        szInfoTitle = bytes( title, 'ascii' ),
        dwInfoFlags = NIIF_USER
    )

    # Display the notification message for the tray item.
    result = ctypes.windll.shell32.Shell_NotifyIconA(
        NIM_MODIFY,
        ctypes.byref( notify_data )
    )

    # Check notification message.
    if bool( result ) == False:
        raise RuntimeError( 'Unable to post notification message.' )
    logging.debug( 'Notification message posted.' )

    # Prepare for event-handling.
    window_message         = ctypes.wintypes.MSG()
    window_message_pointer = ctypes.pointer( window_message )
    result = ctypes.windll.user32.GetMessageA(
        window_message_pointer,
        window_handle,
        0,
        0
    )

    # Enter event-handling loop.
    while( result == True ):
        ctypes.windll.user32.DispatchMessageA(
            ctypes.byref( window_message )
        )
        result = ctypes.windll.user32.GetMessageA(
            window_message_pointer,
            window_handle,
            0,
            0
        )

    logging.debug( 'Notification procedure complete.' )

    # Return exit status.
    return int( window_message.wParam )


#=============================================================================
def hello():
    """
    Hello world with ctypes binding to Win32 API.

    MessageBoxW(
        NULL,
        L"Hello World!",
        L"Greetings",
        ( MB_OK | MB_ICONINFORMATION )
    );
    """
    MB_OK              = 0x00000000
    MB_ICONINFORMATION = 0x00000040
    IDOK               = 1
    result = ctypes.windll.User32.MessageBoxW(
        None,
        'Hello World!',
        'Greetings',
        ( MB_OK | MB_ICONINFORMATION )
    )
    if result != IDOK:
        print( 'OK button was not clicked!' )


#=============================================================================
def main( argv ):
    """
    Script execution entry point

    @param argv List of arguments passed to the script
    @return     Shell exit code (0 = success)
    """

    # imports when using this as a script
    import argparse

    # create and configure an argument parser
    parser = argparse.ArgumentParser(
        description = 'Shell Script',
        add_help    = False
    )
    parser.add_argument(
        '-h',
        '--help',
        default = False,
        help    = 'Display this help message and exit.',
        action  = 'help'
    )
    parser.add_argument(
        '-v',
        '--version',
        default = False,
        help    = 'Display script version and exit.',
        action  = 'version',
        version = __version__
    )
    parser.add_argument(
        '-w',
        '--win32',
        default = False,
        help    = 'Test Win32 API linkage.',
        action  = 'store_true'
    )
    parser.add_argument(
        'message',
        nargs   = '?',
        default = 'You\'ve been bugged!',
        help    = 'The notification message to display.'
    )
    parser.add_argument(
        'title',
        nargs   = '?',
        default = 'Bugme!',
        help    = 'The notification title to display.'
    )

    # parse the arguments
    args = parser.parse_args( argv[ 1 : ] )

    # check for API linkage test
    if args.win32 == True:
        hello()
        result = 0

    # run the notification function
    else:
        result = notify( args.message, args.title )

    #subject = '9B96F0A9-51AD-4031-9306-DEAA0272603F'
    #tuid = uuid.UUID( subject )
    #guid = GUID( subject )
    #print( 's:', subject )
    #print( 'e:', str( tuid ).upper() )
    #print( 'a:', str( guid ) )
    #print( 'self test:', guid._self_test() )

    # return exit status
    return result


#=============================================================================
if __name__ == "__main__":
    sys.exit( main( sys.argv ) )

