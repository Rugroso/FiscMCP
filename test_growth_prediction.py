"""
Test script for business growth prediction tool
"""
import asyncio
from src.main import predict_growth_logic

async def test_growth_prediction():
    """Test the business growth prediction with sample data"""
    
    print("=" * 60)
    print("TEST 1: Negocio Pequeño Saludable")
    print("=" * 60)
    
    response1 = await predict_growth_logic(
        monthly_income=50000,
        monthly_expenses=30000,
        net_profit=20000,
        profit_margin=0.4,
        cash_flow=45000,
        debt_ratio=0.2,
        business_age_years=3,
        employees=5,
        digitalization_score=0.7,
        access_to_credit=True
    )
    
    result1 = response1['data']
    
    print(f"✅ Crecimiento predicho: {result1['predicted_growth_percentage']:.2f}%")
    print(f"📊 Nivel: {result1['growth_level']}")
    print(f"💡 Interpretación: {result1['interpretation']}")
    print(f"📋 Recomendaciones: {len(result1['recommendations'])} consejos")
    for i, rec in enumerate(result1['recommendations'], 1):
        print(f"   {i}. {rec}")
    print(f"📈 Métricas:")
    print(f"   - Margen de utilidad: {result1['metrics']['profit_margin_pct']:.1f}%")
    print(f"   - Ratio de deuda: {result1['metrics']['debt_ratio_pct']:.1f}%")
    print(f"   - Digitalización: {result1['metrics']['digitalization_pct']:.1f}%")
    print()
    
    print("=" * 60)
    print("TEST 2: Negocio con Desafíos")
    print("=" * 60)
    
    response2 = await predict_growth_logic(
        monthly_income=35000,
        monthly_expenses=32000,
        net_profit=3000,
        profit_margin=0.09,
        cash_flow=15000,
        debt_ratio=0.55,
        business_age_years=1,
        employees=2,
        digitalization_score=0.3,
        access_to_credit=False
    )
    
    result2 = response2['data']
    
    print(f"✅ Crecimiento predicho: {result2['predicted_growth_percentage']:.2f}%")
    print(f"📊 Nivel: {result2['growth_level']}")
    print(f"💡 Interpretación: {result2['interpretation']}")
    print(f"📋 Recomendaciones: {len(result2['recommendations'])} consejos")
    for i, rec in enumerate(result2['recommendations'], 1):
        print(f"   {i}. {rec}")
    print(f"📈 Métricas:")
    print(f"   - Margen de utilidad: {result2['metrics']['profit_margin_pct']:.1f}%")
    print(f"   - Ratio de deuda: {result2['metrics']['debt_ratio_pct']:.1f}%")
    print(f"   - Digitalización: {result2['metrics']['digitalization_pct']:.1f}%")
    print()
    
    print("=" * 60)
    print("TEST 3: Negocio Grande Exitoso")
    print("=" * 60)
    
    response3 = await predict_growth_logic(
        monthly_income=300000,
        monthly_expenses=180000,
        net_profit=120000,
        profit_margin=0.40,
        cash_flow=280000,
        debt_ratio=0.25,
        business_age_years=10,
        employees=30,
        digitalization_score=0.95,
        access_to_credit=True
    )
    
    result3 = response3['data']
    
    print(f"✅ Crecimiento predicho: {result3['predicted_growth_percentage']:.2f}%")
    print(f"📊 Nivel: {result3['growth_level']}")
    print(f"💡 Interpretación: {result3['interpretation']}")
    print(f"📋 Recomendaciones: {len(result3['recommendations'])} consejos")
    for i, rec in enumerate(result3['recommendations'], 1):
        print(f"   {i}. {rec}")
    print(f"📈 Métricas:")
    print(f"   - Margen de utilidad: {result3['metrics']['profit_margin_pct']:.1f}%")
    print(f"   - Ratio de deuda: {result3['metrics']['debt_ratio_pct']:.1f}%")
    print(f"   - Digitalización: {result3['metrics']['digitalization_pct']:.1f}%")
    print()
    
    print("=" * 60)
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_growth_prediction())
