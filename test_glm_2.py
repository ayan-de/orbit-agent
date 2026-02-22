from src.config import settings
import httpx

def test():
    key = settings.GLM_API_KEY
    available = []
    try:
        r = httpx.get("https://open.bigmodel.cn/api/paas/v4/models", headers={"Authorization": f"Bearer {key}"})
        if r.status_code == 200:
            available = [m["id"] for m in r.json().get("data", [])]
    except Exception:
        pass
        
    for m in available + ["glm-4-flash", "glm-4", "glm-4-air"]:
        try:
            r = httpx.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": m, "messages": [{"role": "user", "content": "hi"}]}
            )
            print(f"{m}: {r.status_code}")
            if r.status_code == 200:
                print(f"SUCCESS with {m}")
                break
            else:
                print(r.json())
        except Exception as e:
            pass
test()
