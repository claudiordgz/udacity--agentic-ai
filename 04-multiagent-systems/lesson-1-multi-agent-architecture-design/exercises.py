import matplotlib.pyplot as plt
import networkx as nx
import numpy as np




def create_diagram(title, nodes, edges, node_labels=None, node_types=None, edge_labels=None):
    graph = nx.DiGraph()
    
    graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    
    if node_labels is None:
        node_labels = {node: node for node in nodes}
    if node_types is None:
        node_types = {node: 'agent' for node in nodes}
    if edge_labels is None:
        edge_labels = {}

    plt.figure(figsize=(16, 10))
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    
    pos = {}
    horizontal_spacing = 1.5  # Increased spacing
    vertical_spacing = 1.2    # Increased spacing
    
    # Dynamic positioning based on title
    if "Uluru" in title:
        # Original nodes positioning with better spacing
        pos["Visitor Input"] = (0, 0)
        pos["Language Identification"] = (horizontal_spacing, 0)
        pos["Arrernte Language Specialist"] = (2*horizontal_spacing, vertical_spacing)
        pos["Pitjantjatjara Language Specialist"] = (2*horizontal_spacing, -vertical_spacing)
        pos["Knowledge Base Lookup"] = (3*horizontal_spacing, 0)
        
        # New extension nodes positioning with better spacing
        pos["Translation Verification Agent"] = (4*horizontal_spacing, 0)
        pos["Multimodal Media Tool"] = (3*horizontal_spacing, 2.5*vertical_spacing)
        pos["Cultural Sensitivity Checker"] = (5*horizontal_spacing, 0)
        pos["Feedback Collector"] = (0, 2.5*vertical_spacing)
        pos["Response Formatter"] = (6*horizontal_spacing, 0)
        
    elif "E-commerce" in title:
        # E-commerce checkout positioning with improved layout
        # Customer-facing layer
        pos["Customer Interface"] = (0, 0)
        
        # Core orchestration layer
        pos["Cart Manager Agent"] = (horizontal_spacing, 0)
        
        # Validation and pricing layer
        pos["Inventory Agent"] = (2*horizontal_spacing, vertical_spacing)
        pos["Pricing Agent"] = (2*horizontal_spacing, -vertical_spacing)
        
        # Payment processing layer
        pos["Payment Agent"] = (3*horizontal_spacing, 0)
        pos["Fraud Detection Agent"] = (4*horizontal_spacing, vertical_spacing)
        
        # Order management layer
        pos["Order Management Agent"] = (4*horizontal_spacing, -vertical_spacing)
        
        # Fulfillment layer
        pos["Shipping Agent"] = (5*horizontal_spacing, vertical_spacing)
        pos["Notification Agent"] = (5*horizontal_spacing, -vertical_spacing)
        
        # Support and monitoring layer
        pos["Customer Support Agent"] = (6*horizontal_spacing, 0)
        pos["Analytics Agent"] = (3*horizontal_spacing, 2.5*vertical_spacing)
        
    else:
        # Improved default positioning with automatic layout
        pos = nx.spring_layout(nx.DiGraph(edges), k=2, iterations=50, seed=42)
        # Scale the positions to match our spacing
        for node in pos:
            pos[node] = (pos[node][0] * horizontal_spacing * 2, pos[node][1] * vertical_spacing * 2)
    
    node_colors = []
    node_shapes = []
    node_sizes = []
    
    for node in nodes:
        node_type = node_types.get(node, 'agent')
        
        if node_type == 'agent':
            node_colors.append("#6495ED")
            node_shapes.append('o')
            node_sizes.append(2800)
        elif node_type == 'tool':
            node_colors.append("#FFD700")
            node_shapes.append('s')
            node_sizes.append(2600)
        elif node_type == 'user':
            node_colors.append("#FF6347")
            node_shapes.append('d')
            node_sizes.append(2400)
        elif node_type == 'data':
            node_colors.append("#90EE90")
            node_shapes.append('h')
            node_sizes.append(2500)
        else:
            node_colors.append("#C0C0C0")
            node_shapes.append('p')
            node_sizes.append(2300)

    for i, node in enumerate(nodes):
        nx.draw_networkx_nodes(graph, pos, 
                             nodelist=[node],
                             node_color=[node_colors[i]], 
                             node_shape=node_shapes[i],
                             node_size=node_sizes[i],
                             edgecolors='black', 
                             linewidths=1.5, 
                             alpha=0.9)
    
    nx.draw_networkx_edges(graph, pos, 
                         edge_color="black", 
                         arrowsize=25,
                         width=2.0, 
                         alpha=0.9, 
                         arrowstyle='-|>', 
                         connectionstyle="arc3,rad=0.1")

    for node, (x, y) in pos.items():
        plt.text(x, y, node_labels[node], 
                fontsize=10, 
                ha='center', 
                va='center',
                fontweight='bold',
                bbox=dict(facecolor='white', 
                         alpha=0.9, 
                         edgecolor='lightgray', 
                         boxstyle='round,pad=0.3'))
                         
    if edge_labels:
        for edge, label in edge_labels.items():
            x1, y1 = pos[edge[0]]
            x2, y2 = pos[edge[1]]
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2 + 0.25  # Increased offset to prevent overlap
            plt.text(x, y, label, 
                    fontsize=9,  # Smaller font to reduce overlap
                    ha='center',
                    va='center',
                    fontweight='bold',
                    color='darkblue',
                    bbox=dict(facecolor='white', 
                             alpha=0.9,
                             edgecolor='blue',
                             boxstyle='round,pad=0.2'))

    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor="#6495ED", markersize=15, label='Agent'),
        plt.Line2D([0], [0], marker='s', color='w', markerfacecolor="#FFD700", markersize=15, label='Tool/Resource'),
        plt.Line2D([0], [0], marker='d', color='w', markerfacecolor="#FF6347", markersize=15, label='User Interface'),
        plt.Line2D([0], [0], marker='h', color='w', markerfacecolor="#90EE90", markersize=15, label='Data Component')
    ]
    plt.legend(handles=legend_elements, loc='upper right', fontsize=12)

    plt.axis("off")
    plt.tight_layout()
    plt.show()


""" 
Suggested Extensions, Pick One or Mix
1. Add a "Translation Verification Agent"
This agent checks if the translation preserves meaning/cultural context.

Comes after the language specialist and before the response goes to the user.

2. Add a "Multimodal Media Tool"
A tool that retrieves images/audio relevant to the query (e.g., a sound clip of a traditional song or image of a local artifact).

Connects to both the language specialist and the knowledge base.

3. Add a "Feedback Collector"
Captures user feedback after receiving information.

Helps improve future responses and tracks which areas need more detail or clarification.

4. Add a "Cultural Sensitivity Checker" Tool
Ensures that knowledge being returned is appropriate to share (some Indigenous knowledge is restricted or sacred).


"""


def extended_uluru_exercise():
    # Existing Nodes
    nodes = [
        "Visitor Input",
        "Language Identification",
        "Arrernte Language Specialist",
        "Pitjantjatjara Language Specialist",
        "Knowledge Base Lookup",
        # New extension nodes
        "Translation Verification Agent",
        "Multimodal Media Tool",
        "Cultural Sensitivity Checker",
        "Feedback Collector",
        "Response Formatter"
    ]
    
    edges = [
        # Original flow
        ("Visitor Input", "Language Identification"),
        ("Language Identification", "Arrernte Language Specialist"),
        ("Language Identification", "Pitjantjatjara Language Specialist"),
        ("Arrernte Language Specialist", "Knowledge Base Lookup"),
        ("Pitjantjatjara Language Specialist", "Knowledge Base Lookup"),
        ("Knowledge Base Lookup", "Arrernte Language Specialist"),
        ("Knowledge Base Lookup", "Pitjantjatjara Language Specialist"),
        
        # Translation verification flow
        ("Arrernte Language Specialist", "Translation Verification Agent"),
        ("Pitjantjatjara Language Specialist", "Translation Verification Agent"),
        
        # Multimodal media integration
        ("Knowledge Base Lookup", "Multimodal Media Tool"),
        ("Arrernte Language Specialist", "Multimodal Media Tool"),
        ("Pitjantjatjara Language Specialist", "Multimodal Media Tool"),
        
        # Cultural sensitivity checking
        ("Translation Verification Agent", "Cultural Sensitivity Checker"),
        ("Multimodal Media Tool", "Cultural Sensitivity Checker"),
        
        # Response formatting and output
        ("Cultural Sensitivity Checker", "Response Formatter"),
        ("Response Formatter", "Visitor Input"),
        
        # Feedback collection
        ("Visitor Input", "Feedback Collector"),
        ("Feedback Collector", "Language Identification"),
        
        # Back to language specialists for refinement
        ("Translation Verification Agent", "Arrernte Language Specialist"),
        ("Translation Verification Agent", "Pitjantjatjara Language Specialist"),
    ]
    
    node_types = {
        "Visitor Input": "user",
        "Language Identification": "tool",
        "Arrernte Language Specialist": "agent",
        "Pitjantjatjara Language Specialist": "agent",
        "Knowledge Base Lookup": "tool",
        # New extension node types
        "Translation Verification Agent": "agent",
        "Multimodal Media Tool": "tool",
        "Cultural Sensitivity Checker": "tool",
        "Feedback Collector": "tool",
        "Response Formatter": "tool"
    }

    edge_labels = {
        # Original flow labels
        ("Language Identification", "Arrernte Language Specialist"): "Arrernte Query",
        ("Language Identification", "Pitjantjatjara Language Specialist"): "Pitjantjatjara Query",
        ("Knowledge Base Lookup", "Arrernte Language Specialist"): "Cultural Data",
        ("Knowledge Base Lookup", "Pitjantjatjara Language Specialist"): "Cultural Data",
        
        # Translation verification labels
        ("Arrernte Language Specialist", "Translation Verification Agent"): "Translation",
        ("Pitjantjatjara Language Specialist", "Translation Verification Agent"): "Translation",
        
        # Multimodal media labels
        ("Knowledge Base Lookup", "Multimodal Media Tool"): "Media Query",
        ("Arrernte Language Specialist", "Multimodal Media Tool"): "Context",
        ("Pitjantjatjara Language Specialist", "Multimodal Media Tool"): "Context",
        
        # Cultural sensitivity labels
        ("Translation Verification Agent", "Cultural Sensitivity Checker"): "Verified Translation",
        ("Multimodal Media Tool", "Cultural Sensitivity Checker"): "Media Content",
        
        # Response formatting labels
        ("Cultural Sensitivity Checker", "Response Formatter"): "Approved Content",
        ("Response Formatter", "Visitor Input"): "Final Response",
        
        # Feedback labels
        ("Visitor Input", "Feedback Collector"): "User Feedback",
        ("Feedback Collector", "Language Identification"): "Improvement Data",
        
        # Refinement labels
        ("Translation Verification Agent", "Arrernte Language Specialist"): "Revision Request",
        ("Translation Verification Agent", "Pitjantjatjara Language Specialist"): "Revision Request",
    }

    create_diagram(
        "Uluru Cultural Center: Extended System",
        nodes,
        edges,
        None,
        node_types,
        edge_labels
    )
def ecommerce_checkout_architecture():
    """
    E-commerce Checkout Multi-Agent Architecture
    
    This system handles the complete checkout process from cart to order confirmation,
    including inventory management, payment processing, fraud detection, and customer communication.
    """
    
    # Define all agents in the system
    nodes = [
        "Customer Interface",
        "Cart Manager Agent",
        "Inventory Agent", 
        "Pricing Agent",
        "Payment Agent",
        "Fraud Detection Agent",
        "Shipping Agent",
        "Notification Agent",
        "Order Management Agent",
        "Customer Support Agent",
        "Analytics Agent"
    ]
    
    # Define connections between agents with improved orchestration flow
    edges = [
        # Customer interaction flow
        ("Customer Interface", "Cart Manager Agent"),
        ("Cart Manager Agent", "Customer Interface"),
        
        # Cart validation and pricing (parallel processing)
        ("Cart Manager Agent", "Inventory Agent"),
        ("Cart Manager Agent", "Pricing Agent"),
        ("Inventory Agent", "Cart Manager Agent"),
        ("Pricing Agent", "Cart Manager Agent"),
        
        # Checkout orchestration flow
        ("Cart Manager Agent", "Payment Agent"),
        ("Payment Agent", "Fraud Detection Agent"),
        ("Fraud Detection Agent", "Payment Agent"),
        ("Payment Agent", "Order Management Agent"),
        
        # Order fulfillment (parallel processing)
        ("Order Management Agent", "Shipping Agent"),
        ("Order Management Agent", "Notification Agent"),
        ("Shipping Agent", "Notification Agent"),
        
        # Customer support integration
        ("Customer Interface", "Customer Support Agent"),
        ("Order Management Agent", "Customer Support Agent"),
        
        # Analytics and monitoring (real-time data flow)
        ("Order Management Agent", "Analytics Agent"),
        ("Payment Agent", "Analytics Agent"),
        ("Fraud Detection Agent", "Analytics Agent"),
        ("Cart Manager Agent", "Analytics Agent"),
        
        # Support escalation and feedback loops
        ("Customer Support Agent", "Order Management Agent"),
        ("Customer Support Agent", "Payment Agent"),
        ("Analytics Agent", "Cart Manager Agent"),  # Performance feedback
    ]
    
    # Define agent types
    node_types = {
        "Customer Interface": "user",
        "Cart Manager Agent": "agent",
        "Inventory Agent": "agent", 
        "Pricing Agent": "agent",
        "Payment Agent": "agent",
        "Fraud Detection Agent": "agent",
        "Shipping Agent": "agent",
        "Notification Agent": "agent",
        "Order Management Agent": "agent",
        "Customer Support Agent": "agent",
        "Analytics Agent": "agent"
    }
    
    # Define data flow labels with improved clarity
    edge_labels = {
        # Customer interaction
        ("Customer Interface", "Cart Manager Agent"): "Cart Actions",
        ("Cart Manager Agent", "Customer Interface"): "Cart Updates",
        
        # Inventory and pricing (parallel validation)
        ("Cart Manager Agent", "Inventory Agent"): "Stock Validation",
        ("Inventory Agent", "Cart Manager Agent"): "Availability",
        ("Cart Manager Agent", "Pricing Agent"): "Price Calculation",
        ("Pricing Agent", "Cart Manager Agent"): "Final Pricing",
        
        # Payment orchestration flow
        ("Cart Manager Agent", "Payment Agent"): "Checkout Initiated",
        ("Payment Agent", "Fraud Detection Agent"): "Transaction Review",
        ("Fraud Detection Agent", "Payment Agent"): "Risk Decision",
        ("Payment Agent", "Order Management Agent"): "Payment Success",
        
        # Order fulfillment (parallel processing)
        ("Order Management Agent", "Shipping Agent"): "Fulfillment",
        ("Order Management Agent", "Notification Agent"): "Order Created",
        ("Shipping Agent", "Notification Agent"): "Tracking Updates",
        
        # Customer support integration
        ("Customer Interface", "Customer Support Agent"): "Support Request",
        ("Order Management Agent", "Customer Support Agent"): "Order Context",
        
        # Analytics and monitoring (real-time insights)
        ("Order Management Agent", "Analytics Agent"): "Order Metrics",
        ("Payment Agent", "Analytics Agent"): "Payment Analytics",
        ("Fraud Detection Agent", "Analytics Agent"): "Fraud Patterns",
        ("Cart Manager Agent", "Analytics Agent"): "Cart Analytics",
        
        # Support escalation and feedback loops
        ("Customer Support Agent", "Order Management Agent"): "Order Changes",
        ("Customer Support Agent", "Payment Agent"): "Refund Processing",
        ("Analytics Agent", "Cart Manager Agent"): "Performance Insights",
    }
    
    # Create the diagram
    create_diagram(
        "E-commerce Checkout Multi-Agent Architecture",
        nodes,
        edges,
        None,
        node_types,
        edge_labels
    )
    
    # Print detailed agent descriptions
    print("\n" + "="*80)
    print("AGENT ROLES AND RESPONSIBILITIES")
    print("="*80)
    
    agent_descriptions = {
        "Customer Interface": "🎯 User-facing interface for browsing, cart management, and checkout initiation",
        "Cart Manager Agent": "🛒 Core orchestrator managing cart state, coordinating validation and pricing workflows",
        "Inventory Agent": "📦 Real-time inventory tracking, stock availability checks, reservation management",
        "Pricing Agent": "💰 Dynamic pricing calculations, discounts, taxes, shipping costs, promotional offers",
        "Payment Agent": "💳 Payment processing orchestrator, multiple payment methods, PCI compliance",
        "Fraud Detection Agent": "🛡️ Real-time fraud screening, risk assessment, ML-based transaction monitoring",
        "Shipping Agent": "🚚 Shipping method selection, carrier integration, label generation, tracking",
        "Notification Agent": "📱 Multi-channel notifications (email, SMS, push), order updates, confirmations",
        "Order Management Agent": "📋 Order lifecycle orchestrator, fulfillment coordination, status tracking",
        "Customer Support Agent": "🎧 Customer inquiries, order modifications, refunds, issue resolution",
        "Analytics Agent": "📊 Performance monitoring, business intelligence, real-time insights, optimization"
    }
    
    for agent, description in agent_descriptions.items():
        print(f"\n{agent}:")
        print(f"  {description}")
    
    print("\n" + "="*80)
    print("ARCHITECTURE ANALYSIS: BOTTLENECKS & OPTIMIZATION STRATEGIES")
    print("="*80)
    
    bottlenecks = [
        {
            "issue": "Payment Agent: Single point of failure for all transactions",
            "impact": "High - Complete checkout failure",
            "solution": "Implement payment gateway redundancy, circuit breakers, and fallback providers"
        },
        {
            "issue": "Fraud Detection Agent: High latency during ML model inference",
            "impact": "Medium - Checkout delays",
            "solution": "Async processing, model caching, and pre-computed risk scores"
        },
        {
            "issue": "Inventory Agent: Race conditions during high traffic",
            "impact": "High - Overselling risk",
            "solution": "Distributed locking, inventory reservation, and optimistic concurrency control"
        },
        {
            "issue": "Cart Manager Agent: Orchestration complexity",
            "impact": "Medium - Coordination overhead",
            "solution": "Event-driven architecture, message queues, and workflow state machines"
        },
        {
            "issue": "Analytics Agent: Real-time processing bottlenecks",
            "impact": "Low - Delayed insights",
            "solution": "Stream processing, data partitioning, and edge computing"
        },
        {
            "issue": "Customer Support Agent: Peak load handling",
            "impact": "Medium - Customer experience degradation",
            "solution": "Auto-scaling, queue management, and AI-powered first-line support"
        }
    ]
    
    for i, bottleneck in enumerate(bottlenecks, 1):
        print(f"\n{i}. {bottleneck['issue']}")
        print(f"   Impact: {bottleneck['impact']}")
        print(f"   Solution: {bottleneck['solution']}")
    
    print("\n" + "="*80)
    print("ARCHITECTURE PATTERNS IMPLEMENTED")
    print("="*80)
    
    patterns = [
        "🔄 Orchestrator Pattern: Cart Manager Agent coordinates workflow",
        "⚡ Parallel Processing: Inventory + Pricing validation run concurrently",
        "🛡️ Circuit Breaker: Fraud Detection with fallback mechanisms",
        "📊 Event-Driven: Analytics Agent processes real-time events",
        "🎯 Single Responsibility: Each agent has focused domain expertise",
        "🔄 Feedback Loops: Analytics → Cart Manager performance optimization"
    ]
    
    for pattern in patterns:
        print(f"  {pattern}")


if __name__ == "__main__":
    # Run both exercises
    print("Running Uluru Cultural Center Extended System...")
    extended_uluru_exercise()
    
    print("\n" + "="*100)
    print("Running E-commerce Checkout Architecture...")
    ecommerce_checkout_architecture()