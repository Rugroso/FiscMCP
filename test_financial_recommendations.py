"""
Test script for financial recommendations tool
"""
import asyncio
from src.main import get_financial_recommendations_logic

async def test_financial_recommendations():
    """Test the financial recommendations with different scenarios"""
    
    print("=" * 70)
    print("TEST 1: Restaurante con RFC - Buscar créditos y deducciones")
    print("=" * 70)
    
    response1 = await get_financial_recommendations_logic(
        actividad="Restaurante",
        ingresos_mensuales=80000,
        gastos_mensuales=50000,
        tiene_rfc=True,
        regimen_fiscal="RESICO",
        num_empleados=5
    )
    
    result1 = response1['data']
    
    print(f"✅ Salud Financiera: {result1['financial_health']['score']}/100")
    print(f"📊 Nivel: {result1['financial_health']['level']}")
    print(f"💰 Utilidad mensual: ${result1['financial_health']['monthly_profit']:,.2f}")
    print(f"📈 Margen: {result1['financial_health']['profit_margin']}%")
    print()
    
    print(f"💳 Opciones de Crédito: {len(result1['credit_options'])}")
    for i, option in enumerate(result1['credit_options'], 1):
        print(f"   {i}. {option['title']}")
        print(f"      Relevancia: {option['relevance']}%")
        if option.get('source'):
            print(f"      Fuente: {option['source']}")
    print()
    
    print(f"🧾 Deducciones Fiscales: {len(result1['tax_deductions'])}")
    for i, deduction in enumerate(result1['tax_deductions'], 1):
        print(f"   {i}. {deduction['title']}")
        print(f"      Relevancia: {deduction['relevance']}%")
    print()
    
    print(f"💡 Recomendaciones Generales: {len(result1['recommendations'])}")
    for i, rec in enumerate(result1['recommendations'], 1):
        print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
        print(f"      {rec['description']}")
    print()
    
    print("=" * 70)
    print("TEST 2: Freelancer sin RFC - Necesita formalización")
    print("=" * 70)
    
    response2 = await get_financial_recommendations_logic(
        actividad="Diseñador gráfico freelance",
        ingresos_mensuales=25000,
        gastos_mensuales=8000,
        tiene_rfc=False,
        regimen_fiscal=None,
        num_empleados=0
    )
    
    result2 = response2['data']
    
    print(f"✅ Salud Financiera: {result2['financial_health']['score']}/100")
    print(f"📊 Nivel: {result2['financial_health']['level']}")
    print(f"💰 Utilidad mensual: ${result2['financial_health']['monthly_profit']:,.2f}")
    print()
    
    print(f"💡 Recomendaciones: {len(result2['recommendations'])}")
    for i, rec in enumerate(result2['recommendations'], 1):
        print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
        print(f"      Acción: {rec['action']}")
    print()
    
    print("=" * 70)
    print("TEST 3: E-commerce con alto volumen")
    print("=" * 70)
    
    response3 = await get_financial_recommendations_logic(
        actividad="Tienda en línea de ropa",
        ingresos_mensuales=250000,
        gastos_mensuales=180000,
        tiene_rfc=True,
        regimen_fiscal="Persona Física con Actividad Empresarial",
        num_empleados=8
    )
    
    result3 = response3['data']
    
    print(f"✅ Salud Financiera: {result3['financial_health']['score']}/100")
    print(f"📊 Nivel: {result3['financial_health']['level']}")
    print(f"💰 Utilidad mensual: ${result3['financial_health']['monthly_profit']:,.2f}")
    print(f"📈 Margen: {result3['financial_health']['profit_margin']}%")
    print()
    
    print(f"💳 Opciones de Crédito: {len(result3['credit_options'])}")
    for option in result3['credit_options'][:3]:
        print(f"   • {option['title']}")
    print()
    
    print(f"🧾 Deducciones Fiscales: {len(result3['tax_deductions'])}")
    for deduction in result3['tax_deductions'][:3]:
        print(f"   • {deduction['title']}")
    print()
    
    print("=" * 70)
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_financial_recommendations())
