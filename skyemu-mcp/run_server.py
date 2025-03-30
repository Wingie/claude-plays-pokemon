#!/usr/bin/env python3
"""
Script to start the SkyEmu MCP server.

Make sure SkyEmu is running with HTTP Control Server enabled on port 8080
before starting this server.
"""
import argparse
import sys
import os

from skyemu_mcp_server import app, skyemu

def main():
    parser = argparse.ArgumentParser(description="Run the SkyEmu MCP server")
    parser.add_argument("--host", default="localhost", help="SkyEmu HTTP server host (default: localhost)")
    parser.add_argument("--port", type=int, default=8080, help="SkyEmu HTTP server port (default: 8080)")
    parser.add_argument("--mcp-port", type=int, default=None, 
                        help="MCP server port (default: auto-select from MCP protocol)")
    args = parser.parse_args()
    
    # Update SkyEmu client connection parameters if needed
    if args.host != "localhost" or args.port != 8080:
        print(f"Connecting to SkyEmu at {args.host}:{args.port}...")
        # Recreate the client with the specified host and port
        skyemu.__init__(host=args.host, port=args.port)
    
    # Verify SkyEmu connection
    try:
        if skyemu.ping():
            print(f"Successfully connected to SkyEmu at {args.host}:{args.port}")
            
            # Get and display emulator status
            status = skyemu.get_status()
            print(f"Emulator: {status.get('emulator', 'Unknown')}")
            print(f"Run mode: {status.get('run-mode', 'Unknown')}")
            print(f"ROM loaded: {status.get('rom-loaded', False)}")
            if 'rom-path' in status:
                print(f"ROM path: {status['rom-path']}")
    except Exception as e:
        print(f"Error connecting to SkyEmu: {e}")
        print("Make sure SkyEmu is running with the HTTP Control Server enabled.")
        sys.exit(1)
    
    print("\nStarting SkyEmu MCP Server...")
    print("Use Claude or another MCP-compatible LLM to control the emulator.")
    print("Press Ctrl+C to stop the server")
    
    # Start the MCP server
    if args.mcp_port:
        app.run(transport="stdio", port=args.mcp_port)
    else:
        app.run(transport="stdio")

if __name__ == "__main__":
    main()
