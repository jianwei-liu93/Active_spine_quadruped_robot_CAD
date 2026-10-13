"""Use the already configured local Blender MCP over its stdio interface."""
import asyncio, json, sys, base64
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
PROMPT="Let's start some blender animation work and generate some videos using the blender MCP, keep files in a structured way in the /home/jianwei/freeCAD_projects/Active_spine_quadruped_robot_CAD project/repo as before"
async def main():
    command=StdioServerParameters(command='/home/jianwei/.local/bin/uvx',args=['--offline','mcp-for-blender'])
    async with stdio_client(command) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            if sys.argv[1]=='list':
                print((await session.list_tools()).model_dump_json(indent=2))
            else:
                args={'user_prompt':PROMPT}
                if sys.argv[1]=='execute_blender_code': args['code']=Path(sys.argv[2]).read_text()
                if sys.argv[1]!='execute_blender_code' and len(sys.argv)>2: args.update(json.loads(Path(sys.argv[2]).read_text()))
                result=await session.call_tool(sys.argv[1],args)
                for i,block in enumerate(result.content):
                    if block.type=='image':
                        path=Path(__file__).resolve().parents[2]/'reports/animation'/('mcp_'+sys.argv[1]+'_'+str(i)+'.png')
                        path.write_bytes(base64.b64decode(block.data));print(json.dumps({'image':str(path)}))
                    elif block.type=='text':print(block.text)
                if result.isError: raise RuntimeError('MCP returned isError')
asyncio.run(main())
