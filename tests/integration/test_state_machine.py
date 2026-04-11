from enum import Enum
from dataclasses import dataclass
from semantic_state_machine.state_machine import AuditContext, AuditedStateMachine


class DocState(Enum):
    DRAFT = 1
    REVIEW = 2
    APPROVED = 3
    PUBLISHED = 4


class DocEvent(Enum):
    SUBMIT = 1
    APPROVE = 2
    REJECT = 3
    PUBLISH = 4


@dataclass
class DocumentContext(AuditContext[DocState, DocEvent]):
    doc_id: str = ""
    reviewer: str | None = None
    is_public: bool = False
    rejection_count: int = 0


def test_document_approval_workflow_integration():
    """
    Simulates a full document approval workflow:
    DRAFT --SUBMIT--> REVIEW --APPROVE--> APPROVED --PUBLISH--> PUBLISHED
                        |                  ^
                        +--REJECT----------+ (back to REVIEW after edits)
    Note: For simplicity, REJECT goes back to REVIEW in this mock model.
    """
    sm = AuditedStateMachine[DocState, DocEvent, DocumentContext]()

    @sm.transition(DocState.DRAFT, DocEvent.SUBMIT, DocState.REVIEW)
    def submit_doc(ctx: DocumentContext):
        ctx.reviewer = "Alice"

    @sm.transition(DocState.REVIEW, DocEvent.APPROVE, DocState.APPROVED)
    def approve_doc(ctx: DocumentContext):
        pass

    @sm.transition(DocState.REVIEW, DocEvent.REJECT, DocState.REVIEW)
    def reject_doc(ctx: DocumentContext):
        ctx.rejection_count += 1

    @sm.transition(DocState.APPROVED, DocEvent.PUBLISH, DocState.PUBLISHED)
    def publish_doc(ctx: DocumentContext):
        ctx.is_public = True

    # 1. Start as DRAFT
    ctx = DocumentContext(doc_id="DOC-001")
    current_state = DocState.DRAFT

    # 2. Submit for Review
    current_state = sm.handle_transition(ctx, current_state, DocEvent.SUBMIT)
    assert current_state == DocState.REVIEW
    assert ctx.reviewer == "Alice"

    # 3. Reject twice (simulating revisions)
    current_state = sm.handle_transition(ctx, current_state, DocEvent.REJECT)
    current_state = sm.handle_transition(ctx, current_state, DocEvent.REJECT)
    assert current_state == DocState.REVIEW
    assert ctx.rejection_count == 2

    # 4. Approve
    current_state = sm.handle_transition(ctx, current_state, DocEvent.APPROVE)
    assert current_state == DocState.APPROVED

    # 5. Publish
    current_state = sm.handle_transition(ctx, current_state, DocEvent.PUBLISH)
    assert current_state == DocState.PUBLISHED
    assert ctx.is_public is True

    # 6. Verify audit trail
    expected_audit = [
        (DocState.DRAFT, DocEvent.SUBMIT),
        (DocState.REVIEW, DocEvent.REJECT),
        (DocState.REVIEW, DocEvent.REJECT),
        (DocState.REVIEW, DocEvent.APPROVE),
        (DocState.APPROVED, DocEvent.PUBLISH),
    ]
    assert ctx._audit == expected_audit
