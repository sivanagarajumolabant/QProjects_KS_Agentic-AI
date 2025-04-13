from langgraph.graph import StateGraph, START,END
from src.langgraph_agentic_ai.state.state import State
from src.langgraph_agentic_ai.nodes.sdlc_node import SDLCNode   


class GraphBuilder:

    def __init__(self,model):
        self.llm=model
        self.graph_builder=StateGraph(State)

        
    def sdlc_graph(self):
        """
        """
        self.sdlc_node=SDLCNode(self.llm)
        
        self.graph_builder.add_node("user_requirements", self.sdlc_node.user_requirement)
        self.graph_builder.add_node("auto_generate_user_stories", self.sdlc_node.auto_generate_user_stories)
        self.graph_builder.add_node("product_owner_review", self.sdlc_node.product_owner_review)
        self.graph_builder.add_node("revise_user_story", self.sdlc_node.revise_user_story)
        self.graph_builder.add_node("generate_design_doc", self.sdlc_node.generate_design_doc)
        self.graph_builder.add_node("design_doc_reviewer", self.sdlc_node.design_doc_reviewer)
        self.graph_builder.add_node("generate_code", self.sdlc_node.generate_code)
        self.graph_builder.add_node("code_reviewer", self.sdlc_node.code_reviewer)
        self.graph_builder.add_node("fix_code_after_code_review", self.sdlc_node.fix_code_after_code_review)
        self.graph_builder.add_node("security_reviewer", self.sdlc_node.security_reviewer)
        self.graph_builder.add_node("generate_test_cases", self.sdlc_node.generate_test_cases)
        self.graph_builder.add_node("fix_code_after_security_review", self.sdlc_node.fix_code_after_security_review)
        self.graph_builder.add_node("test_cases_reviewer", self.sdlc_node.test_cases_reviewer)
        self.graph_builder.add_node("fix_test_cases_after_review", self.sdlc_node.fix_test_cases_after_review)
        self.graph_builder.add_node("qa_testing", self.sdlc_node.qa_testing)
        self.graph_builder.add_node("fix_code_after_qa_testing", self.sdlc_node.fix_code_after_qa_testing)

        self.graph_builder.add_edge(START, "user_requirements")
        self.graph_builder.add_edge("user_requirements", "auto_generate_user_stories")
        self.graph_builder.add_edge("auto_generate_user_stories", "product_owner_review")
        self.graph_builder.add_conditional_edges("product_owner_review", self.sdlc_node.product_route, {"revise_user_story": "revise_user_story", "generate_design_doc": "generate_design_doc"})
        self.graph_builder.add_edge("revise_user_story", "auto_generate_user_stories")
        self.graph_builder.add_edge("generate_design_doc", "design_doc_reviewer")
        self.graph_builder.add_conditional_edges("design_doc_reviewer", self.sdlc_node.design_doc_route, {"generate_code": "generate_code", "generate_design_doc": "generate_design_doc"})
        self.graph_builder.add_edge("generate_code", "code_reviewer")
        self.graph_builder.add_conditional_edges("code_reviewer", self.sdlc_node.code_route, {"fix_code_after_code_review": "fix_code_after_code_review", "security_reviewer": "security_reviewer"})
        self.graph_builder.add_edge("fix_code_after_code_review", "generate_code")
        self.graph_builder.add_conditional_edges("security_reviewer", self.sdlc_node.security_route, {"generate_test_cases": "generate_test_cases", "fix_code_after_security_review": "fix_code_after_security_review"})
        self.graph_builder.add_edge("fix_code_after_security_review", "generate_code")
        self.graph_builder.add_edge("generate_test_cases", "test_cases_reviewer")
        self.graph_builder.add_conditional_edges("test_cases_reviewer", self.sdlc_node.test_cases_route, {"fix_test_cases_after_review": "fix_test_cases_after_review", "qa_testing": "qa_testing"})
        self.graph_builder.add_edge("fix_test_cases_after_review", "generate_test_cases")
        self.graph_builder.add_conditional_edges("qa_testing", self.sdlc_node.qa_test_route, {"fix_code_after_qa_testing": "fix_code_after_qa_testing", "end": END})
        self.graph_builder.add_edge("fix_code_after_qa_testing", "generate_code")

    
    
    
    def setup_graph(self, usecase: str):
        """
        Sets up the graph for the selected use case.
        """
            
        if usecase == "SDLC":
            self.sdlc_graph()
            
        return self.graph_builder.compile()
    
    