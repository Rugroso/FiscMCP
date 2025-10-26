"""
Test para verificar el formato de la recomendación fiscal
Verifica que se generen los 3 puntos solicitados
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from src.gemini import gemini_client

async def test_recommendation_format():
    """Prueba el formato de la recomendación con un perfil simple"""
    
    print("🧪 Probando formato de recomendación fiscal...")
    print("=" * 60)
    
    # Perfil de prueba simple
    profile = {
        "actividad": "Venta de comida preparada en establecimiento",
        "ingresos_anuales": 500000,
        "estado": "Ciudad de México",
        "tiene_rfc": False,
        "regimen_actual": None
    }
    
    # Contexto simulado (normalmente vendría de la búsqueda RAG)
    context = """
[1] Régimen Simplificado de Confianza — Personas Físicas
Fuente: https://www.sat.gob.mx/consulta/09471/conoce-el-regimen-simplificado-de-confianza
El Régimen Simplificado de Confianza (RESICO) es para personas físicas con ingresos anuales de hasta $3.5 millones de pesos. Tasa del 1% al 2.5% según ingresos. Facilita cumplimiento fiscal.

[2] Pasos para obtener tu RFC — SAT
Fuente: https://www.sat.gob.mx/tramites/operacion/28753/obten-tu-rfc-con-la-clave-unica-de-registro-de-poblacion-(curp)
Para obtener tu RFC necesitas: CURP, acta de nacimiento, comprobante de domicilio. Puedes tramitarlo en línea o en oficinas del SAT.

[3] e.firma (Firma Electrónica) — SAT
Fuente: https://www.sat.gob.mx/tramites/92445/obten-tu-certificado-de-e.firma
La e.firma es tu identidad digital ante el SAT. Necesaria para hacer trámites en línea. Requiere: RFC activo, CURP, identificación oficial.
"""
    
    try:
        print("\n📋 Perfil de prueba:")
        print(f"   - Actividad: {profile['actividad']}")
        print(f"   - Ingresos: ${profile['ingresos_anuales']:,}")
        print(f"   - Estado: {profile['estado']}")
        print(f"   - Tiene RFC: {profile['tiene_rfc']}")
        
        print("\n🤖 Generando recomendación con Gemini...")
        recommendation = await gemini_client.generate_recommendation(profile, context)
        
        print("\n✅ Recomendación generada:")
        print("=" * 60)
        print(recommendation)
        print("=" * 60)
        
        # Verificar que contiene los 3 elementos esperados
        print("\n🔍 Verificando estructura...")
        
        checks = {
            "Régimen fiscal": False,
            "Pasos de formalización": False,
            "Fuentes": False
        }
        
        recommendation_lower = recommendation.lower()
        
        # Check 1: Menciona régimen fiscal
        if any(word in recommendation_lower for word in ['régimen', 'regimen', 'resico', 'simplificado']):
            checks["Régimen fiscal"] = True
            print("   ✅ Menciona régimen fiscal")
        else:
            print("   ❌ No menciona régimen fiscal claramente")
        
        # Check 2: Menciona pasos de formalización
        if any(word in recommendation_lower for word in ['rfc', 'e.firma', 'pasos', 'formalización', 'formalizacion']):
            checks["Pasos de formalización"] = True
            print("   ✅ Incluye pasos de formalización")
        else:
            print("   ❌ No incluye pasos de formalización")
        
        # Check 3: Incluye fuentes
        if any(word in recommendation_lower for word in ['fuente', 'sat.gob.mx', 'https://', 'http://']):
            checks["Fuentes"] = True
            print("   ✅ Incluye fuentes")
        else:
            print("   ❌ No incluye fuentes")
        
        # Resumen
        passed = sum(checks.values())
        total = len(checks)
        
        print("\n" + "=" * 60)
        print(f"📊 Resultado: {passed}/{total} elementos verificados")
        
        if passed == total:
            print("🎉 ¡Formato correcto! La recomendación incluye los 3 puntos solicitados")
            return True
        else:
            print(f"⚠️  Faltan {total - passed} elemento(s)")
            return False
            
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_recommendation_format())
    sys.exit(0 if success else 1)
