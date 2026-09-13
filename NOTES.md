# the communication is hapenig via  the master but not via HTTPS. It should be done using GOOGLE agent connectivity or some other secure channel. The current implementation is insecure and should not be used in production

```bash
    def main() -> None:  # pragma: no cover
        """EHLO, build role, then run manager or served-peer loop forever."""
        import os

        from agents.deliberator.llm_factory import build_llm, key_env_var
        from agents.deliberator.poll import find_pending, review_pm_node
        from kernel.graph_env import build_graph_from_env
        from kernel.work_loop import work_loop

        settings = DeliberatorSettings()
        master_url = os.environ.get("MASTER_URL", "http://master:8000")
        pubkey = master_public_key_from_env()
        activate_agent(master_url, settings.identity, public_key_pem=pubkey)
        graph = build_graph_from_env()
        llm = build_llm(
            settings.llm_provider,
            api_key=os.environ.get(key_env_var(settings.llm_provider)),
            model=settings.model_for_role(settings.peer_role or "judge"),
            max_tokens=settings.max_tokens,
            effort=settings.effort,
        )
```
