from app.llm.provider import MockChatModel
from langchain_core.messages import HumanMessage


def test_mock_chat_model_stitches_findings_together():
    llm = MockChatModel()
    prompt = (
        "Question: what's the status of order 3?\n\n"
        "Findings:\n"
        "[mysql] Order 3 for Marc Dupont is currently 'delivered', total $249.50.\n"
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    assert "delivered" in result.content
    assert "249.50" in result.content


def test_mock_chat_model_handles_no_findings():
    llm = MockChatModel()
    result = llm.invoke([HumanMessage(content="Question: what is the meaning of life?\n\nFindings:\n")])
    assert "could not find" in result.content.lower()
