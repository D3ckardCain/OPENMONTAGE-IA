"""Official public YouTube research; no earnings inference or persistent cache."""
from jsonschema import validate
from tools.base_tool import BaseTool, ToolResult, ToolTier, ToolRuntime, ToolStability, ResourceProfile
from .youtube_client import YouTube, Filters

class YouTubeResearch(BaseTool):
    name = "youtube_research"
    version = "0.1.0"
    provider = "youtube_official"
    tier = ToolTier.SOURCE
    runtime = ToolRuntime.LOCAL
    stability = ToolStability.BETA
    capability = "youtube_research"
    capabilities = ["youtube_research"]
    dependencies = ["env:YOUTUBE_API_KEY"]
    idempotency_key_fields = []
    side_effects = ["read_youtube_data_api"]
    resource_profile = ResourceProfile(network_required=True)
    install_instructions = "Set YOUTUBE_API_KEY locally. No paid API fallback."
    input_schema = {"type":"object", "additionalProperties":False,
        "required":["mode","query"], "properties":{
        "mode":{"enum":["search","channel"]}, "query":{"type":"string","minLength":1},
        "pages":{"type":"integer","minimum":1,"maximum":20},
        "filters":{"type":"object","additionalProperties":False,"properties":{
            **{k:{"type":"integer","minimum":0} for k in ("min_seconds","max_seconds","min_views","max_views","min_subscribers","max_subscribers")},
            "language":{"type":"string"},"strict_language":{"type":"boolean"},
            "format":{"enum":["any","short_candidate","over_3m"]}}},
        "region":{"type":"string","pattern":"^[A-Z]{2}$"},
        "after":{"type":"string"},"before":{"type":"string"}}}

    def execute(self, inputs):
        try:
            validate(inputs, self.input_schema)
            client = YouTube()
            filters = Filters(**inputs.get("filters", {}))
            pages = inputs.get("pages", 1)
            if inputs["mode"] == "channel":
                if any(k in inputs for k in ("region","after","before")):
                    raise ValueError("Channel mode does not accept search-only filters")
                data = client.channel(inputs["query"], filters, pages)
            else:
                data = client.search(inputs["query"], filters,
                    inputs.get("region"), inputs.get("after"), inputs.get("before"), pages)
            return ToolResult(success=True, data=data, artifacts=[], cost_usd=0)
        except Exception:
            # Never expose request URLs, credentials or transport exception strings.
            return ToolResult(success=False, error="YOUTUBE_QUERY_FAILED: check inputs, local key, network and quota", data={"stale_fallback":False})
