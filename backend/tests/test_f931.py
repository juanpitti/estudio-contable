from app.f931.generador import generar_txt_f931


def test_generar_txt_con_registro_encabezado():
    txt = generar_txt_f931(
        cuit_empleador="20273965239",
        periodo="202608",
        empleados=[],
    )
    lineas = txt.strip().split("\n")
    assert lineas[0].startswith("01")
    assert "20273965239" in lineas[0]
    assert "202608" in lineas[0]


def test_generar_txt_con_empleado():
    txt = generar_txt_f931(
        cuit_empleador="20273965239",
        periodo="202608",
        empleados=[{
            "cuit": "20345678901",
            "apellido_nombre": "GARCIA JUAN",
            "remuneracion": "100000.00",
            "aportes": "17000.00",
            "contribuciones": "21000.00",
            "situacion_revista": "1",
        }],
    )
    lineas = txt.strip().split("\n")
    assert len(lineas) == 3
    assert lineas[1].startswith("02")
    assert "20345678901" in lineas[1]


def test_generar_txt_totales_correctos():
    txt = generar_txt_f931(
        cuit_empleador="20273965239",
        periodo="202608",
        empleados=[
            {"cuit": "20345678901", "apellido_nombre": "A", "remuneracion": "100000.00", "aportes": "17000.00", "contribuciones": "21000.00", "situacion_revista": "1"},
            {"cuit": "20345678902", "apellido_nombre": "B", "remuneracion": "200000.00", "aportes": "34000.00", "contribuciones": "42000.00", "situacion_revista": "1"},
        ],
    )
    lineas = txt.strip().split("\n")
    totales = lineas[-1]
    assert totales.startswith("03")
