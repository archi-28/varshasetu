"""Mock-first notification abstraction; no credentials required."""
class MockNotificationService:
    def send(self, message: str) -> dict:
        return {"success": True, "status": "Alert generated successfully", "message": message}
