# Multi-Agent SDLC Architecture Diagram
Student ID: 202321006

## 5-Phase Gated Pipeline

```mermaid
graph TD
    User([Human Requirement]) --> Planner[Planner Agent]
    Planner -->|requirement.json| Gate1{Gate: Spec Quality}
    
    Gate1 -- Pass --> Architect[Architect Agent]
    Gate1 -- Fail --> Planner
    
    Architect -->|task_graph.json + DAG| Gate2{Gate: Arch Validation}
    
    Gate2 -- Pass --> Coder[Coder Agent x N]
    Gate2 -- Fail --> Architect
    
    Coder -->|PR / Diff Artifacts| Gate3{Gate: Local Validation}
    
    Gate3 -- Pass --> QA[QA Agent]
    Gate3 -- Fail --> Coder
    
    QA -->|Review Report| Gate4{Gate: Global Integration}
    
    Gate4 -- Pass --> Wrapup[Wrapup Agent]
    Gate4 -- Fail --> Coder
    
    Wrapup -->|LESSON.md + pipeline_state.json| Prod([Final Delivery])
```

## Agent Roles and Responsibilities
| Agent | Role | Artifacts | Responsibility |
|-------|------|-----------|----------------|
| **Planner** | Product Manager | `requirement.json` | Requirement parsing, AC definition |
| **Architect** | Software Architect | `task.json`, DAG | Dependency analysis, task decomposition |
| **Coder** | Developer | Pull Request, Diffs | Implementation in Ralph Loop |
| **QA** | Quality Assurance | Review Report | Integration testing, security review |
| **Wrapup** | Knowledge Manager | `LESSON.md`, State Update | Knowledge capture, final merging |
