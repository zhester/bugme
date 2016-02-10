/*****************************************************************************

main.c

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

Usage
=====

    bugme [message [title]]

Without any arguments, the message is "You've been bugged!", and the title is
"Bugme!".  The first argument will replace the default message with a string
of your choice (up to 255 characters).  The second argument will replace the
default title with a string of your choice (up to 63 characters).

*****************************************************************************/

/*============================================================================
Includes
============================================================================*/

#include <windows.h>
#include <tchar.h>

#include <stdlib.h>
#include <shellapi.h>
#include <strsafe.h>

/*============================================================================
Macros
============================================================================*/

#define APPLICATION_MESSAGE_ID ( WM_USER + 24 )
#define EXIT_USAGE_ERROR ( 1 )
#define EXIT_API_ERROR   ( 2 )
#define EXIT_UNKN_ERROR  ( 9 )

/*============================================================================
Types and Structures
============================================================================*/

/*============================================================================
Memory Constants
============================================================================*/

LPCTSTR                 CLASS_NAME      = _T( "notify_class" );
                                        /* application class name           */
LPCTSTR                 DEFAULT_MESSAGE = _T( "You've been bugged!" );
                                        /* fall-back notification message   */
LPCTSTR                 DEFAULT_TITLE   = _T( "Bugme!" );
                                        /* fall-back notification title     */

/*============================================================================
Module Variables
============================================================================*/

/*============================================================================
Module Prototypes
============================================================================*/

#ifndef UNICODE
static void free_array(                 /* free array of pointed-to things  */
    void**              array,          /* pointer to array of pointers     */
    int                 count           /* number of items in the array     */
);
#endif

#ifndef UNICODE
static LPSTR* wc2mb_array(              /* convert array of strings         */
    LPCWSTR*            strings,        /* wide-char array of strings       */
    int                 count           /* number of strings in array       */
);                                      /* multi-byte array of string       */
#endif

/*============================================================================
Implementation
============================================================================*/

/*==========================================================================*/
LRESULT CALLBACK window_procedure(      /* window handling procedure        */
    HWND                hWnd,           /* window handle                    */
    UINT                uMsg,           /* window message                   */
    WPARAM              wParam,         /* message argument 1               */
    LPARAM              lParam          /* message argument 2               */
) {                                     /* returns 0 if message was handled */

    /*--------------------------------------------------------------------
    Local Variables
    --------------------------------------------------------------------*/
    NOTIFYICONDATA      notify_data;

    /*--------------------------------------------------------------------
    Select message handler.
    --------------------------------------------------------------------*/
    switch( uMsg ) {

        /*----------------------------------------------------------------
        Handle application-specific message.
        ----------------------------------------------------------------*/
        case APPLICATION_MESSAGE_ID:
            switch( LOWORD( lParam ) ) {
                case NIN_BALLOONTIMEOUT:
                case NIN_BALLOONHIDE:
                case NIN_BALLOONUSERCLICK:
                    DestroyWindow( hWnd );
                    UnregisterClass( CLASS_NAME, GetModuleHandle( NULL ) );
                    break;
            }
            break;

        /*----------------------------------------------------------------
        Message posted when the window is released.
        ----------------------------------------------------------------*/
        case WM_DESTROY:
            memset( &notify_data, 0, sizeof( NOTIFYICONDATA ) );
            notify_data.cbSize = sizeof( NOTIFYICONDATA );
            notify_data.hWnd   = hWnd;
            Shell_NotifyIcon( NIM_DELETE, &notify_data );
            PostQuitMessage( 0 );
            break;

        /*----------------------------------------------------------------
        All other messages.
        ----------------------------------------------------------------*/
        default:
            return DefWindowProc( hWnd, uMsg, wParam, lParam );
            break;
    }

    /*--------------------------------------------------------------------
    Message handled in this procedure.
    --------------------------------------------------------------------*/
    return 0;
}


/*==========================================================================*/
int WINAPI WinMain(                     /* program entry point              */
    HINSTANCE           hInstance,      /* handle to program instance       */
    HINSTANCE           hPrevInst,      /* handle to previous instance      */
    LPTSTR              lpCmdLine,      /* pointer to command-line string   */
    int                 nShowCmd        /* initial window display setting   */
) {                                     /* return program exit status       */

    /*--------------------------------------------------------------------
    Local Macros
    --------------------------------------------------------------------*/
    #define TITLE_SIZE   (  64 )        /* size of title string buffer      */
    #define MESSAGE_SIZE ( 256 )        /* size of message string buffer    */

    /*--------------------------------------------------------------------
    Macros to clean up repeated code when copying strings.
    --------------------------------------------------------------------*/

    #define mscopy_early( _d, _s )                                          \
        result = StringCchCopyN(                                            \
            ( _d ),                                                         \
            sizeof( _d ),                                                   \
            ( _s ),                                                         \
            lstrlen( _s )                                                   \
        );                                                                  \
        if( result != S_OK ) {                                              \
            return EXIT_API_ERROR;                                          \
        }

    #define mscopy_late( _d, _s )                                           \
        result = StringCchCopyN(                                            \
            ( _d ),                                                         \
            sizeof( _d ),                                                   \
            ( _s ),                                                         \
            lstrlen( _s )                                                   \
        );                                                                  \
        if( result != S_OK ) {                                              \
            DestroyWindow( window_handle );                                 \
            UnregisterClass( CLASS_NAME, class_info.hInstance );            \
            return EXIT_API_ERROR;                                          \
        }

    /*--------------------------------------------------------------------
    Local Variables
    --------------------------------------------------------------------*/
    LPCTSTR             application_name = _T( "bugme" );
                                        /* internal application name        */
    int                 argc;           /* argument count                   */
    LPTSTR*             argv;           /* argument list                    */
    LPWSTR*             arguments;      /* list of argument string pointers */
    WNDCLASSEX          class_info;     /* application class memory         */
    ATOM                class_resource; /* application class resource       */
    HICON               icon_handle;    /* icon handle                      */
    NOTIFYICONDATA      notify_data;    /* notify icon API memory           */
    TCHAR               notify_message[ MESSAGE_SIZE ];
                                        /* notification message             */
    TCHAR               notify_title[ TITLE_SIZE ];
                                        /* notification title               */
    BOOL                result;         /* result of API calls              */
    LPCTSTR             tooltip          = _T( "Bugme!" );
                                        /* icon tooltip text                */
    HWND                window_handle;  /* application window handle        */
    MSG                 window_message; /* window message memory            */

    /*--------------------------------------------------------------------
    Parse command line.
    --------------------------------------------------------------------*/
    arguments = CommandLineToArgvW( GetCommandLineW(), &argc );
    if( arguments == NULL ) {
        return EXIT_UNKN_ERROR;
    }

    /*--------------------------------------------------------------------
    Check for arguments.
    --------------------------------------------------------------------*/
    if( argc > 1 ) {

        /*----------------------------------------------------------------
        Conditional ASCII conversion.
        ----------------------------------------------------------------*/
        #ifndef UNICODE
            argv = wc2mb_array( ( LPCWSTR* ) arguments, argc );
            if( argv == NULL ) {
                LocalFree( arguments );
                return EXIT_UNKN_ERROR;
            }
        #else
            argv = arguments;
        #endif

        /*----------------------------------------------------------------
        Copy arguments for later use.
        ----------------------------------------------------------------*/
        mscopy_early( notify_message, argv[ 1 ] );
        if( argc > 2 ) {
            mscopy_early( notify_title, argv[ 2 ] );
        }
        else {
            mscopy_early( notify_title, DEFAULT_TITLE );
        }

        /*----------------------------------------------------------------
        Release parsed argument memory.
        ----------------------------------------------------------------*/
        LocalFree( arguments );
    }

    /*--------------------------------------------------------------------
    No arguments given.
    --------------------------------------------------------------------*/
    else {

        /*----------------------------------------------------------------
        Use some test strings.
        ----------------------------------------------------------------*/
        mscopy_early( notify_message, DEFAULT_MESSAGE );
        mscopy_early( notify_title, DEFAULT_TITLE );
    }

    /*--------------------------------------------------------------------
    Configure the window class for the parent window.
    --------------------------------------------------------------------*/
    memset( &class_info, 0, sizeof( WNDCLASSEX ) );
    class_info.cbSize        = sizeof( WNDCLASSEX );
    class_info.hInstance     = hInstance;
    class_info.lpszClassName = CLASS_NAME;
    class_info.lpfnWndProc   = window_procedure;

    /*--------------------------------------------------------------------
    Register the window class.
    --------------------------------------------------------------------*/
    class_resource = RegisterClassEx( &class_info );
    if( class_resource == 0 ) {
        return EXIT_API_ERROR;
    }

    /*--------------------------------------------------------------------
    Create the parent window (never displayed).
    --------------------------------------------------------------------*/
    window_handle = CreateWindowEx(
        0,
        CLASS_NAME,
        application_name,
        ( WS_OVERLAPPED | WS_SYSMENU ),
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        NULL,
        NULL,
        class_info.hInstance,
        NULL
    );
    if( window_handle == NULL ) {
        UnregisterClass( CLASS_NAME, class_info.hInstance );
        return EXIT_API_ERROR;
    }

    /*--------------------------------------------------------------------
    Load the icon displayed on the taskbar and the notification.
    Note: The "a" is used to reference the embedded icon set in bugme.rc.
    --------------------------------------------------------------------*/
    icon_handle = LoadImage(
        class_info.hInstance,
        _T( "a" ),
        IMAGE_ICON,
        0,
        0,
        LR_DEFAULTSIZE
    );
    if( icon_handle == NULL ) {
        DestroyWindow( window_handle );
        UnregisterClass( CLASS_NAME, class_info.hInstance );
        return EXIT_API_ERROR;
    }

    /*--------------------------------------------------------------------
    Configure the notification icon.
    --------------------------------------------------------------------*/
    memset( &notify_data, 0, sizeof( NOTIFYICONDATA ) );
    notify_data.cbSize           = sizeof( NOTIFYICONDATA );
    notify_data.hWnd             = window_handle;
    notify_data.uFlags           = ( NIF_ICON | NIF_MESSAGE | NIF_TIP );
    notify_data.uCallbackMessage = APPLICATION_MESSAGE_ID;
    notify_data.hIcon            = icon_handle;
    mscopy_late( notify_data.szTip, tooltip );

    /*--------------------------------------------------------------------
    Add the notification icon to the taskbar.
    --------------------------------------------------------------------*/
    result = Shell_NotifyIcon( NIM_ADD, &notify_data );
    if( result == FALSE ) {
        DestroyWindow( window_handle );
        UnregisterClass( CLASS_NAME, class_info.hInstance );
        return EXIT_API_ERROR;
    }

    /*--------------------------------------------------------------------
    Update notification to allow posting messages.
    --------------------------------------------------------------------*/
    notify_data.uFlags      = NIF_INFO;
    notify_data.dwInfoFlags = NIIF_USER;
    mscopy_late( notify_data.szInfo, notify_message );
    mscopy_late( notify_data.szInfoTitle, notify_title );

    /*--------------------------------------------------------------------
    Post a notification message by modifying the icon.
    --------------------------------------------------------------------*/
    result = Shell_NotifyIcon( NIM_MODIFY, &notify_data );
    if( result == FALSE ) {
        DestroyWindow( window_handle );
        UnregisterClass( CLASS_NAME, class_info.hInstance );
        return EXIT_API_ERROR;
    }

    /*--------------------------------------------------------------------
    Enter window message handling loop.
    --------------------------------------------------------------------*/
    result = GetMessage( &window_message, window_handle, 0, 0 );
    while( result == TRUE ) {
        DispatchMessage( &window_message );
        result = GetMessage( &window_message, window_handle, 0, 0 );
    }

    /*--------------------------------------------------------------------
    Return message handling status to shell.
    --------------------------------------------------------------------*/
    return ( int ) window_message.wParam;
}


/*==========================================================================*/
#ifndef UNICODE
static void free_array(                 /* free array of pointed-to things  */
    void**              array,          /* pointer to array of pointers     */
    int                 count           /* number of items in the array     */
) {

    /*------------------------------------------------------------------------
    Local Variables
    ------------------------------------------------------------------------*/
    int                 index;      /* array index                          */

    /*------------------------------------------------------------------------
    Check pointer.
    ------------------------------------------------------------------------*/
    if( array == NULL ) {
        return;
    }

    /*------------------------------------------------------------------------
    Free each item in the array.
    ------------------------------------------------------------------------*/
    for( index = 0; index < count; ++index ) {
        if( array[ index ] != NULL ) {
            free( array[ index ] );
        }
    }

    /*------------------------------------------------------------------------
    Free the array of pointers.
    ------------------------------------------------------------------------*/
    free( array );
}
#endif


/*=========================================================================*/
#ifndef UNICODE
static LPSTR* wc2mb_array(              /* convert array of strings         */
    LPCWSTR*            strings,        /* wide-char array of strings       */
    int                 count           /* number of strings in array       */
) {                                     /* multi-byte array of string       */

    /*------------------------------------------------------------------------
    Cleanly stops the string conversion loop.
    ------------------------------------------------------------------------*/
    #define stop_conversion()                           \
        free_array( ( void** ) result, ( index + 1 ) ); \
        result = NULL;                                  \
        break

    /*------------------------------------------------------------------------
    Local Variables
    ------------------------------------------------------------------------*/
    int                 conv_result;
                                    /* result of string conversion          */
    int                 index;      /* array index                          */
    int                 length;     /* lengths of strings                   */
    char**              result;     /* list of converted strings            */
    int                 size;       /* size of new buffer                   */
    BOOL                used_default;
                                    /* flag if conversion defaulted         */

    /*------------------------------------------------------------------------
    Allocate an array of string pointers.
    ------------------------------------------------------------------------*/
    result = calloc( count, sizeof( char* ) );

    /*------------------------------------------------------------------------
    Check allocation.
    ------------------------------------------------------------------------*/
    if( result == NULL ) {
        return NULL;
    }

    /*------------------------------------------------------------------------
    Convert each string to multi-byte representation.
    ------------------------------------------------------------------------*/
    for( index = 0; index < count; ++index ) {

        /*--------------------------------------------------------------------
        Get length of wide-character input string.
        --------------------------------------------------------------------*/
        length = wcslen( strings[ index ] );

        /*--------------------------------------------------------------------
        Converted string needs enough room for a terminator.
        --------------------------------------------------------------------*/
        size = length + 1;

        /*--------------------------------------------------------------------
        Allocate storage for the same number of bytes.
        --------------------------------------------------------------------*/
        result[ index ] = calloc( size, sizeof( char ) );

        /*--------------------------------------------------------------------
        Check allocation.
        --------------------------------------------------------------------*/
        if( result[ index ] == NULL ) {

            /*----------------------------------------------------------------
            Free any allocated memory, and stop converting strings.
            ----------------------------------------------------------------*/
            stop_conversion();
        }

        /*--------------------------------------------------------------------
        Perform the conversion to a multi-byte string.
        --------------------------------------------------------------------*/
        conv_result = WideCharToMultiByte(
            CP_ACP,                 /* use context's codepage               */
            0,                      /* default conversion settings          */
            strings[ index ],       /* source string to convert             */
            length,                 /* length of the string to convert      */
            result[ index ],        /* conversion destination memory        */
            size,                   /* size of destination memory           */
            NULL,                   /* use system default character         */
            &used_default           /* flag if conversion defaulted         */
        );

        /*--------------------------------------------------------------------
        Check the conversion.
        --------------------------------------------------------------------*/
        if( conv_result != length ) {

            /*----------------------------------------------------------------
            Free any allocated memory, and stop converting strings.
            ----------------------------------------------------------------*/
            stop_conversion();
        }
    }

    /*------------------------------------------------------------------------
    Return list of converted strings (or NULL on failure).
    ------------------------------------------------------------------------*/
    return result;
}
#endif

