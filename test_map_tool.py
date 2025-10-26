#!/usr/bin/env python3
"""
Test de la herramienta open_map_location
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Implementación de prueba de la lógica de open_map_location
def test_open_map_location_logic(location_type: str, place_id: Optional[str] = None, search_query: Optional[str] = None):
    """
    Test de la lógica de open_map_location sin decoradores MCP
    """
    try:
        # Validar el tipo de ubicación
        if location_type not in ["bank", "sat"]:
            return {
                'success': False,
                'error': "Tipo de ubicación inválido",
                'message': "location_type debe ser 'bank' o 'sat'"
            }
        
        # Construir el deep link para la app
        base_url = "fiscai://map"
        params = [f"type={location_type}"]
        
        if place_id:
            params.append(f"placeId={place_id}")
        
        if search_query:
            params.append(f"query={search_query}")
        
        deep_link = f"{base_url}?{'&'.join(params)}"
        
        # Construir mensaje descriptivo
        location_name = "Banorte" if location_type == "bank" else "oficinas del SAT"
        
        if place_id:
            message = f"Abriendo mapa enfocado en un {location_name} específico"
        elif search_query:
            message = f"Abriendo mapa buscando: {search_query}"
        else:
            message = f"Abriendo mapa con {location_name} cercanos"
        
        return {
            'success': True,
            'data': {
                'deep_link': deep_link,
                'location_type': location_type,
                'place_id': place_id,
                'search_query': search_query,
                'user_message': f"📍 {message}. El mapa se abrirá automáticamente."
            },
            'message': message
        }
        
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'message': "Error generando enlace al mapa"
        }

def test_open_map_location():
    """Test de la herramienta open_map_location"""
    
    print("\n" + "="*70)
    print("  🗺️  TEST: open_map_location")
    print("="*70)
    
    # Test 1: Abrir mapa de bancos
    print("\n📍 Test 1: Abrir mapa de bancos")
    result1 = test_open_map_location_logic(location_type="bank")
    if result1.get('success'):
        print(f"✅ {result1.get('message')}")
        print(f"   Deep Link: {result1['data']['deep_link']}")
        print(f"   Mensaje usuario: {result1['data']['user_message']}")
    else:
        print(f"❌ Error: {result1.get('error')}")
    
    # Test 2: Abrir mapa de oficinas SAT
    print("\n📍 Test 2: Abrir mapa de oficinas SAT")
    result2 = test_open_map_location_logic(location_type="sat")
    if result2.get('success'):
        print(f"✅ {result2.get('message')}")
        print(f"   Deep Link: {result2['data']['deep_link']}")
        print(f"   Mensaje usuario: {result2['data']['user_message']}")
    else:
        print(f"❌ Error: {result2.get('error')}")
    
    # Test 3: Abrir mapa con place_id específico
    print("\n📍 Test 3: Abrir mapa con place_id")
    result3 = test_open_map_location_logic(
        location_type="bank",
        place_id="ChIJ1234567890"
    )
    if result3.get('success'):
        print(f"✅ {result3.get('message')}")
        print(f"   Deep Link: {result3['data']['deep_link']}")
        print(f"   Mensaje usuario: {result3['data']['user_message']}")
    else:
        print(f"❌ Error: {result3.get('error')}")
    
    # Test 4: Abrir mapa con query de búsqueda
    print("\n📍 Test 4: Abrir mapa con búsqueda")
    result4 = test_open_map_location_logic(
        location_type="bank",
        search_query="Banorte Reforma"
    )
    if result4.get('success'):
        print(f"✅ {result4.get('message')}")
        print(f"   Deep Link: {result4['data']['deep_link']}")
        print(f"   Mensaje usuario: {result4['data']['user_message']}")
    else:
        print(f"❌ Error: {result4.get('error')}")
    
    # Test 5: Error - tipo de ubicación inválido
    print("\n📍 Test 5: Tipo de ubicación inválido (debe fallar)")
    result5 = test_open_map_location_logic(location_type="invalid")
    if not result5.get('success'):
        print(f"✅ Error detectado correctamente: {result5.get('error')}")
    else:
        print(f"❌ Debería haber fallado pero no lo hizo")
    
    # Test 6: Combinar place_id y search_query
    print("\n📍 Test 6: Combinar place_id y search_query")
    result6 = test_open_map_location_logic(
        location_type="sat",
        place_id="ChIJABCDEF",
        search_query="Centro tributario"
    )
    if result6.get('success'):
        print(f"✅ {result6.get('message')}")
        print(f"   Deep Link: {result6['data']['deep_link']}")
        print(f"   Verifica que incluya ambos parámetros")
    else:
        print(f"❌ Error: {result6.get('error')}")
    
    print("\n" + "="*70)
    print("  ✅ TESTS DE open_map_location COMPLETADOS")
    print("="*70)
    print("\n💡 Nota: Esta es una prueba de la lógica. Para probar el MCP completo,")
    print("   usa el inspector de FastMCP con: fastmcp dev server.py")

if __name__ == "__main__":
    test_open_map_location()
