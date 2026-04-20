# Dependency DAG and Parallelization Tier Analysis
Student ID: 202321006

## Scenario: Implementing Secure Document Storage
| Task ID | Title | Dependencies | Tier |
|---------|-------|--------------|------|
| TASK-001 | KMS Encryption Utility | None | 0 |
| TASK-002 | S3 Bucket Configuration | None | 0 |
| TASK-003 | Database Schema | None | 0 |
| TASK-004 | File Upload Service | TASK-001, TASK-002 | 1 |
| TASK-005 | Metadata CRUD | TASK-003 | 1 |
| TASK-006 | Integration Tests | TASK-004, TASK-005 | 2 |

## Parallelization Strategy
- **Tier 0**: Parallel execution of base utilities.
- **Tier 1**: Parallel implementation of core services.
- **Tier 2**: Final validation gate.
