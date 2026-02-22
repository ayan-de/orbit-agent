from src.config import settings
import httpx

def test():
    key = settings.GLM_API_KEY
    for m in ["glm-4", "glm-4-flash", "glm-3-turbo", "glm-4-plus"]:
        try:
            r = httpx.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": m, "messages": [{"role": "user", "content": "hi"}]}
            )
            print(f"{m}: {r.status_code}")
            if r.status_code != 200:
                print(r.json())
        except Exception as e:
            print(f"{m} error {e}")
test()
