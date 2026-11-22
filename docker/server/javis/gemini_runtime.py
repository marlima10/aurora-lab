"""Aurora policy around the original Javis Gemini engine and MCP hub."""
import inspect
import fnmatch

VAULT='/brains/auroralab'
READ_TOOLS=('auroralab__aurora_web_search','auroralab__aurora_web_read','auroralab__aurora_fitness_summary','auroralab__aurora_finance_accounts',
 'auroralab__aurora_finance_summary','auroralab__aurora_recipes','auroralab__aurora_shopping_lists',
 'auroralab__aurora_model_library',
 'javis_read_file','javis_list_dir','javis_search_files')

def scoped(signature,args,kwargs):
    params=signature.bind_partial(*args,**kwargs).arguments
    requested=params.get('tool_allowlist')
    params.update(vault_root=VAULT,include_plugins=False,include_ambient=False,
                  staging=False,workspace_root=None,coding_ctx_cua_phien=None,force_lazy=False)
    params['tool_allowlist']=[name for name in READ_TOOLS if requested is None or any(fnmatch.fnmatchcase(name,p) for p in requested)]
    return {k:v for k,v in params.items() if k in signature.parameters}

def install(main):
    import mcp_hub
    original=mcp_hub.discover_all;signature=inspect.signature(original)
    async def discover(*args,**kwargs):
        tools,route=await original(**scoped(signature,args,kwargs))
        return [t for t in tools if t.get('fn',t.get('name')) in READ_TOOLS],{k:v for k,v in route.items() if k in READ_TOOLS}
    inventory=mcp_hub.registry_inventory;inventory_signature=inspect.signature(inventory)
    def registry(*args,**kwargs):
        tools,route=inventory(**scoped(inventory_signature,args,kwargs))
        return [t for t in tools if t.get('fn',t.get('name')) in READ_TOOLS],{k:v for k,v in route.items() if k in READ_TOOLS}
    mcp_hub.discover_all=discover;mcp_hub.registry_inventory=registry
    fetch=main._fetch_provider_models
    async def models(provider,settings):
        if provider!='gemini':return await fetch(provider,settings)
        key=settings.get('gemini_api_key')
        if not key:return None
        import httpx
        async with httpx.AsyncClient(timeout=20) as client:
            response=await client.get('https://generativelanguage.googleapis.com/v1beta/models',headers={'x-goog-api-key':key})
            response.raise_for_status()
            values=response.json().get('models',[])
        ids=[x.get('name','').split('/')[-1] for x in values if 'generateContent' in x.get('supportedGenerationMethods',[])]
        return sorted(main._loc_model_chat(ids,main._GEMINI_KHONG_CHAT)) or None
    main._fetch_provider_models=models
