.DEFAULT_GOAL := help
.PHONY: help install install-dev dev dev-host build preview check clean clean-all \
        new-week new-lab sync-syllabus status

# ── Configuration ────────────────────────────────────────────────────────────

NPM         := pnpm
ASTRO       := $(NPM) run astro --
CONTENT_DIR := src/content/docs

# ── Help ─────────────────────────────────────────────────────────────────────

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n\nTargets:\n"} \
	      /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# ── Dependencies ─────────────────────────────────────────────────────────────

install: ## Install dependencies (pnpm install --frozen-lockfile)
	$(NPM) install --frozen-lockfile

install-dev: ## Install dependencies (pnpm install, updates lock file)
	$(NPM) install

# ── Development ──────────────────────────────────────────────────────────────

dev: ## Start dev server at localhost:4321
	$(NPM) run dev

dev-host: ## Start dev server exposed on network (for DGX/remote access)
	$(NPM) run dev -- --host 0.0.0.0

# ── Build & Preview ──────────────────────────────────────────────────────────

build: ## Build the static site to ./dist/
	$(NPM) run build

preview: build ## Build then preview the built site
	$(NPM) run preview

check: ## Type-check the project (astro check)
	$(ASTRO) check

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts (.astro/, dist/)
	rm -rf dist .astro

clean-all: clean ## Remove build artifacts AND node_modules
	rm -rf node_modules

# ── Content Helpers ──────────────────────────────────────────────────────────

# Usage: make new-week N=07
new-week: ## Scaffold a new week file. Usage: make new-week N=07
ifndef N
	$(error N is required. Usage: make new-week N=07)
endif
	@FILE="$(CONTENT_DIR)/weeks/week-$(N).mdx"; \
	if [ -f "$$FILE" ]; then echo "$$FILE already exists"; exit 1; fi; \
	printf '%s\n' \
		'---' \
		'title: "$(N)주차: 제목을 입력하세요"' \
		'description: 설명을 입력하세요' \
		'week: $(N)' \
		'phase: 1' \
		'phase_title: Phase 이름' \
		'date: ""' \
		'theory_topics:' \
		'  - 주제1' \
		'lab_topics:' \
		'  - 실습1' \
		'assignment: "Lab XX: 과제명"' \
		'assignment_due: ""' \
		'difficulty: 중급' \
		'estimated_time: 4시간' \
		'---' \
		'' \
		> "$$FILE"; \
	printf '%s\n' \
		"import { Aside, Steps, Badge, Card, CardGrid } from '@astrojs/starlight/components';" \
		'' \
		'## 이론 (Theory)' \
		'' \
		'### 오늘의 학습 목표' \
		'' \
		'<CardGrid>' \
		'  <Card title="개념 관점" icon="open-book">TODO</Card>' \
		'  <Card title="설계 관점" icon="seti:config">TODO</Card>' \
		'  <Card title="구현 관점" icon="pencil">TODO</Card>' \
		'  <Card title="운영 관점" icon="rocket">TODO</Card>' \
		'</CardGrid>' \
		'' \
		'TODO' \
		'' \
		'## 실습 (Practicum)' \
		'' \
		'<Steps>' \
		'1. **TODO**' \
		'</Steps>' \
		'' \
		'## 과제 (Assignment)' \
		'' \
		'<div class="assignment-box">' \
		'' \
		'### Lab XX: 제목' \
		'' \
		'**제출 마감**: TODO' \
		'' \
		'</div>' \
		'' \
		'## 핵심 정리' \
		'' \
		'1. TODO' \
		'' \
		'## 더 읽을거리' \
		'' \
		'- TODO' \
		>> "$$FILE"; \
	echo "Created: $$FILE"

# Usage: make new-lab N=05
new-lab: ## Scaffold a new lab file. Usage: make new-lab N=05
ifndef N
	$(error N is required. Usage: make new-lab N=05)
endif
	@FILE="$(CONTENT_DIR)/labs/lab-$(N).mdx"; \
	if [ -f "$$FILE" ]; then echo "$$FILE already exists"; exit 1; fi; \
	printf '%s\n' \
		'---' \
		'title: "Lab $(N): 제목을 입력하세요"' \
		'description: 설명을 입력하세요' \
		'week: 1' \
		'difficulty: 중급' \
		'estimated_time: 4시간' \
		'assignment_due: ""' \
		'---' \
		'' \
		> "$$FILE"; \
	printf '%s\n' \
		"import { Steps, Aside, Badge } from '@astrojs/starlight/components';" \
		'' \
		'<Badge text="중급" variant="caution" /> <Badge text="마감: TODO" variant="note" />' \
		'' \
		'## 목표' \
		'' \
		'TODO' \
		'' \
		'## 제출물' \
		'' \
		'`assignments/lab-$(N)/[학번]/`에 PR:' \
		'' \
		'- [ ] TODO' \
		>> "$$FILE"; \
	echo "Created: $$FILE"

# ── Sync ─────────────────────────────────────────────────────────────────────

sync-syllabus: ## Copy root syllabus.md into docs (keeps both in sync)
	@if [ -f syllabus.md ]; then \
	  cp syllabus.md $(CONTENT_DIR)/syllabus.md; \
	  echo "Synced syllabus.md → $(CONTENT_DIR)/syllabus.md"; \
	else \
	  echo "syllabus.md not found in project root"; exit 1; \
	fi

# ── Status ───────────────────────────────────────────────────────────────────

status: ## Show content file counts
	@echo "Weekly notes : $$(ls $(CONTENT_DIR)/weeks/*.mdx 2>/dev/null | wc -l | tr -d ' ') / 16"
	@echo "Lab files    : $$(ls $(CONTENT_DIR)/labs/lab-*.mdx 2>/dev/null | wc -l | tr -d ' ') / 12"
	@echo "Total pages  : $$(find $(CONTENT_DIR) -name '*.md' -o -name '*.mdx' | wc -l | tr -d ' ')"
	@echo "Dist size    : $$(du -sh dist 2>/dev/null | cut -f1 || echo 'not built')"
