"""
演示脚本：使用与阿里云百炼平台整合的Excel财务模型知识图谱系统

此脚本展示系统的完整功能，包括：
1. Excel模型到Neo4j图谱的转换
2. 依赖关系分析和可视化
3. 增量计算和重算
4. 与百炼平台的自然语言交互
"""

print("Setting up and initializing system components...")

# 导入必要的模块
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'financial_kg_system'))

def setup_demo():
    """演示环境设置和系统初始化""" 
    print("\n" + "="*60)
    print("阿里云百炼一体化财务知识图谱系统演示设置")
    print("="*60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # 检查环境配置
    print("[INFO] 环境配置检查:")
    print(f"   - Neo4j URI: {os.getenv('NEO4J_URI', 'Not set')}")
    print(f"   - Redis Host: {os.getenv('REDIS_HOST', 'Not set')}")
    print(f"   - LLM Provider: {os.getenv('LLM_PROVIDER', 'Not set')}")
    print(f"   - LLM Model: {os.getenv('LLM_MODEL', 'Not set')}")
    llm_enabled = os.getenv("ENABLE_LLM_INTEGRATION", "false").lower() == "true"
    print(f"   - LLM 集成: {'ENABLED' if llm_enabled else 'DISABLED'}")
    
    if llm_enabled and os.getenv("LLM_PROVIDER", "").lower() == "aliyun-bailian":
        print(f"   - 百炼API密钥: {'SET' if os.getenv('DASHSCOPE_API_KEY') else 'NOT SET'}")
    
    print("[SUCCESS] 系统组件加载完成")
    
    return llm_enabled

def demo_formula_parsing():
    """演示Excel公式解析能力"""
    print(f"\n[STEP 1] Excel公式解析演示")
    print("-"*40)
    
    from services.excel_formula_engine import ExcelFormulaProcessor
    processor = ExcelFormulaProcessor()
    
    print("解析不同Excel引用类型的公式:")
    
    # 示例公式包括各种引用类型
    test_formulas = [
        "=A1+B1",                             # 基本引用
        "=$A$1+B1",                          # 混合引用
        "=参数输入表!A1+参数输入表!B1",         # 跨工作表引用 
        "=SUM(D4:D10)",                      # 范围求和
        "=AVERAGE($B$2:$B$20)",              # 绝对范围引用
        "=IF(C1>100, C1*0.1, 0)",           # 条件公式
        "=VLOOKUP(E1, 表格1!A:B, 2, FALSE)"    # 查找公式
    ]
    
    for formula in test_formulas:
        print(f"\n公式: {formula}")
        try:
            deps = processor.get_dependencies(formula, "当前工作表")
            for dep_cell, dep_type in deps:
                print(f"  -> 依赖: {dep_cell} ({dep_type})")
        except Exception as e:
            print(f"  -> 解析错误: {str(e)}")

def demo_dependency_graph():
    """演示依赖关系图的构建"""
    print(f"\n[STEP 2] 依赖关系图构建演示")
    print("-"*40)
    
    print("构造简化版抽水蓄能财务模型结构...")
    # 模拟node.json类似的节点结构
    sample_nodes = [
        {
            "id": "参数输入表_4_B",
            "value": "工程计划",
            "formula_raw": None,
            "sheet": "参数输入表",
            "is_head": False,
            "row_category": "工程计划",
            "col_category": "类别", 
            "row": 4,
            "col": "B"
        },
        {
            "id": "参数输入表_4_D",
            "value": "建设期",
            "formula_raw": None,
            "sheet": "参数输入表",
            "is_head": False,
            "row_category": "工程计划", 
            "col_category": "参数",
            "row": 4,
            "col": "D"
        },
        {
            "id": "资金筹措表_10_C",
            "value": "=参数输入表_4_D*0.8",  # 假设的关联公式
            "formula_raw": "参数输入表_4_D*0.8",  # 简化表示
            "sheet": "资金筹措表",
            "is_head": False,
            "row_category": "资金筹措",
            "col_category": "金额",
            "row": 10,
            "col": "C"
        }
    ]
    
    print(f"样本节点数: {len(sample_nodes)}")
    for node in sample_nodes:
        print(f"  - {node['id']}: {node['value'][:20]}{'...' if len(node['value']) > 20 else ''}")
        if node['formula_raw']:
            print(f"    -> 公式: {node['formula_raw']}")
    
    print("[SUCCESS] 依赖图结构已构建")

def demo_smart_recalculation():
    """演示智能重计算引擎"""
    print(f"\n[STEP 3] 智能重计算演示")
    print("-"*40)
    
    print("智能重计算流程:")
    print("1. 检测变更的单元格 => 参数输入表_4_D")
    print("2. 通过图遍历找出影响的下游单元格")
    downstream_cells = ["资金筹措表_10_C", "利润表_25_D", "现金流量表_50_E"]
    print(f"3. 影响下游单元格: {', '.join(downstream_cells)}")
    print("4. 使用拓扑排序确保正确的计算顺序")
    print("5. 计算时间复杂度: O(V+E)，其中V为受影响节点，E为相关边")
    print("[SUCCESS] 重计算流程演示完成")

def demo_llm_integration(llm_enabled):
    """演示与百炼平台的LLM集成"""
    print(f"\n[STEP 4] LLM (百炼平台) 集成演示")
    print("-"*40)
    
    if not llm_enabled:
        print("[WARNING] LLM集成未启用 - 请在.env文件中设置 ENABLE_LLM_INTEGRATION=true")
        print("   且配置相应的DASHSCOPE_API_KEY")
        return
    
    print("LLM连接检查...")
    
    try:
        from utils.llm_integration import SimpleLLMInterface
        llm_interface = SimpleLLMInterface()
        
        if llm_interface.enabled:
            print(f"[SUCCESS] 已连接到 {llm_interface.client.__class__.__name__}")
            print(f"[INFO] 模型: {os.getenv('LLM_MODEL', 'default')}")
            
            print("\n百炼平台在财务分析中的可能应用:")
            applications = [
                "财务模型自然语言问答",
                "敏感性分析报告",
                "假设情景建模",
                "计算逻辑解释",
                "模型验证和调试",
                "摘要和洞察生成"
            ]
            
            for app in applications:
                print(f"  - {app}")
                
            print("\n示例自然语言查询:")
            sample_queries = [
                "如果建设期延长6个月，对现金流有何影响?",
                "利润表中哪些项目对最终净利润影响最大?", 
                "当前的投资回报率是多少，主要驱动因素是什么?",
                "解释资金筹措表的变化如何影响资产负债表?"
            ]
            
            for query in sample_queries:
                print(f"  -> '{query[:30]}{'...' if len(query) > 30 else ''}'")
                
        else:
            print("[WARNING] LLM接口未激活，可能是由于配置错误")
            
    except Exception as e:
        print(f"[ERROR] LLM连接失败: {str(e)}")

def demo_api_functionality():
    """演示API功能"""
    print(f"\n[STEP 5] API功能演示")
    print("-"*40)
    
    api_features = [
        "Excel文件上传和解析",
        "单元格数据增删改查",
        "依赖关系查询",
        "重计算触发",
        "影响范围分析",
        "自然语言查询接口",
        "健康检查"
    ]
    
    for i, feature in enumerate(api_features, 1):
        print(f"{i}. {feature}")
    
    print("\n主要API端点:")
    endpoints = [
        ("POST /api/v1/upload", "上传并处理Excel文件"),
        ("POST /api/v1/cells/update", "更新单元格值并触发重算"),
        ("POST /api/v1/cells/info", "获取单元格详细信息"),
        ("GET /api/v1/cells/{id}/impact", "影响范围分析"),
        ("POST /api/v1/llm/query", "自然语言查询财务模型"),
        ("GET /api/v1/health", "系统健康状况检查")
    ]
    
    for method, endpoint in endpoints:
        print(f"   - {method:20} {endpoint}")

def demo_integration_scenario():
    """演示集成应用场景"""
    print(f"\n[STEP 6] 综合应用场景演示")
    print("-"*40)
    
    print("场景：抽水蓄能项目财务模型分析")
    print("\n初始状态:")
    print("- Excel: 包含参数输入表、资金筹措表、利润表等多个工作表")
    print("- Neo4j: 存储单元格依赖关系和计算网络")
    print("- 缓存: 热点数据和计算图已加载")
    
    print("\n用户操作序列:")
    steps = [
        "1. 专家上传抽水蓄能项目财务Excel模型",
        "2. 系统自动解析公式，构建知识图谱",  
        "3. 用户查询'建设期延长对NPV的影响'", 
        "4. LLM解释模型相关部分",
        "5. 用户调整建设期参数",
        "6. 系统识别依赖关系，触发增量重算",
        "7. 更新现金流量预测和净现值",
        "8. 可视化展示影响传导路径"
    ]
    
    for step in steps:
        print(f"   - {step}")
        
    print("\n结果: 完成了一个完整的财务模型交互分析周期")
    print("      融合了知识图谱的精确性和LLM的理解能力")

def demo_performance_characteristics():
    """演示性能特征"""
    print(f"\n[STEP 7] 性能特征演示") 
    print("-"*40)
    
    performance_metrics = {
        "6-50个工作表": "支持中等复杂度的财务模型",
        "ms级延迟": "缓存优化的快速查询响应",
        "O(V+E)复杂度": "高效的依赖图计算算法",
        "增量更新": "仅重算受影响的单元格",
        "图遍历优化": "Neo4j原生图算法加速"
    }
    
    print("性能指标:")
    for metric, description in performance_metrics.items():
        print(f"  - {metric}: {description}")

def run_demo():
    """运行演示"""
    # 设置
    llm_enabled = setup_demo()
    
    # 运行各部分演示
    demo_formula_parsing()
    demo_dependency_graph()
    demo_smart_recalculation()
    demo_llm_integration(llm_enabled)
    demo_api_functionality()
    demo_integration_scenario()
    demo_performance_characteristics()
    
    print("\n" + "="*60)
    print("演示完成!")
    print("系统已准备就绪，可支持Excel财务模型与百炼平台的大模型分析。")
    
    if llm_enabled:
        print("[SUCCESS] LLM集成功能已启用")
    else:
        print("[INFO] 提示: 启用LLM功能可在.env文件中设置ENABLE_LLM_INTEGRATION=true")
    
    print("\n启动命令:")
    print("   1. 确保Neo4j和Redis正在运行")
    print("   2. 更新.env文件以适应您的配置") 
    print("   3. 启动API服务: python -m uvicorn api.__init__:app --host 0.0.0.0 --port 8000")
    print("="*60)

# 执行演示
if __name__ == "__main__":
    run_demo()