class ContextManager:
    def __init__(self, limit=200000):
        self.limit = limit
        self.history = []

    def add_event(self, event_type, content):
        self.history.append({"type": event_type, "content": content})
        self._prune_if_necessary()

    def _prune_if_necessary(self):
        # Implementation of sliding window pruning
        pass
