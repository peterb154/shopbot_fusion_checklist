import json,sys,mcp
mcp.start()
src=open(sys.argv[1]).read()
print(mcp.call("fusion_mcp_execute",{"featureType":"script","object":{"script":src}}))
