import sys
import json
import logging

# Set up logging to stderr so it doesn't corrupt stdout JSON-RPC stream
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("circana_mcp_server")

def handle_list_tools():
    return {
        "tools": [
            {
                "name": "audience-build",
                "description": "Constructs a target shopper cohort segment from historical purchase data.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string", "description": "Name of the target product brand."},
                        "spend_criteria": {"type": "string", "description": "Segmentation criteria (e.g. lapsed, heavy)."}
                    },
                    "required": ["product_name"]
                }
            },
            {
                "name": "audience-size",
                "description": "Calculates target match sizing and reach metrics across activation channels.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "audience_id": {"type": "string", "description": "Audience ID returned by build-audience."},
                        "partner_options": {"type": "string", "description": "Comma-separated target channels."}
                    },
                    "required": ["audience_id"]
                }
            }
        ]
    }

def handle_call_tool(name, arguments):
    logger.info(f"mcp_server: Calling tool {name} with args {arguments}")
    if name == "audience-build":
        product_name = arguments.get("product_name", "Selected Product")
        spend_criteria = arguments.get("spend_criteria", "lapsed")
        clean_name = product_name.upper().replace(' ', '-').replace("'", "")
        aud_id = f"AUD-{clean_name}-999"
        
        result = {
            "status": "Created",
            "audience_id": aud_id,
            "product_name": product_name,
            "shoppers_isolated": 350000,
            "message": f"Successfully materialized cohort for {product_name} containing 350K historical shoppers."
        }
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }
    elif name == "audience-size":
        audience_id = arguments.get("audience_id", "AUD-DIET-PEPSI-999")
        partner_options = arguments.get("partner_options", "LiveRamp,Google")
        
        # Sizing calculations
        original_size = 350000
        scaled_size = 1200000
        reach_pct = 85.0
        
        result = {
            "audience_id": audience_id,
            "product_name": "Diet Pepsi 12pk",
            "original_size": original_size,
            "scaled_size": scaled_size,
            "reach_percentage": reach_pct,
            "partners": partner_options.split(",")
        }
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }
    else:
        raise ValueError(f"Unknown tool: {name}")

def main():
    logger.info("Circana MCP Tool Server started (listening on stdin).")
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            # Initialization handshake
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "circana-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": handle_list_tools()
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": handle_call_tool(tool_name, arguments)
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # Print response to stdout
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            sys.stderr.flush()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run as HTTP Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="HTTP Server Host")
    parser.add_argument("--port", type=int, default=8080, help="HTTP Server Port")
    args = parser.parse_known_args()[0]
    
    if args.http:
        from fastapi import FastAPI, Request
        import uvicorn
        
        app = FastAPI(title="Circana MCP Server HTTP Mode")
        
        @app.get("/tools")
        def list_tools():
            return handle_list_tools()
            
        @app.post("/tools/call")
        async def call_tool(req: Request):
            body = await req.json()
            name = body.get("name")
            arguments = body.get("arguments", {})
            if not name and "params" in body:
                params = body["params"]
                name = params.get("name")
                arguments = params.get("arguments", {})
            
            logger.info(f"HTTP MCP: Calling tool {name} with args {arguments}")
            try:
                res = handle_call_tool(name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "result": res
                }
            except Exception as e:
                logger.error(f"HTTP MCP Tool call error: {e}")
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        main()
