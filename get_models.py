from src.config import settings
import httpx

def test():
    key = settings.GLM_API_KEY
    try:
        r = httpx.get(
            "https://open.bigmodel.cn/api/paas/v4/models",
            headers={"Authorization": f"Bearer {key}"}
        )
        print(r.status_code)
        if r.status_code == 200:
            models = r.json()
            print([m["id"] for m in models.get("data", [])])
        else:
            print(r.text)
    except Exception as e:
        print(e)
test()
