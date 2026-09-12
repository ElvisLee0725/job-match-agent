.PHONY: start backend frontend

# Run backend + frontend together; Ctrl+C stops both.
start:
	@trap 'kill 0' EXIT INT TERM; \
	$(MAKE) backend & \
	$(MAKE) frontend & \
	wait

backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --port 8000 --reload

frontend:
	cd frontend && npm run dev
