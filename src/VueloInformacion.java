
public class VueloInformacion {
	private String id;
	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	private String origen;
	private String destino;
	private String hora_start;
	private String hora_end;
	private String mes;
	private String dia;
	private String hora_real;
	private boolean diaSiguinte;

	public boolean isDiaSiguinte() {
		return diaSiguinte;
	}

	public void setDiaSiguinte(boolean diaSiguinte) {
		this.diaSiguinte = diaSiguinte;
	}

	public VueloInformacion(String id,String origen, String destino, String hora_start, String hora_end, String mes, String dia) {
		this.id = id;
		this.origen = origen;
		this.destino = destino;
		this.hora_start = hora_start;
		this.hora_real = hora_end;
		this.mes = mes;
		this.dia = dia;
		if (hora_end.contains("+1")) {
			this.diaSiguinte = true;
			this.hora_end = hora_end.substring(0, 5);
		} else {
			this.hora_end = hora_end;
		}
	}

	public String getOrigen() {
		return origen;
	}

	public void setOrigen(String origen) {
		this.origen = origen;
	}

	public String getDestino() {
		return destino;
	}

	public void setDestino(String destino) {
		this.destino = destino;
	}

	public String getHora_start() {
		return hora_start;
	}

	public void setHora_start(String hora_start) {
		this.hora_start = hora_start;
	}

	public String getHora_end() {
		return hora_real;
	}

	public void setHora_end(String hora_end) {
		this.hora_end = hora_end;
	}

	public String getmes() {
		return mes;
	}

	public void setmes(String mes) {
		this.mes = mes;
	}

	public String getdia() {
		return dia;
	}

	public void setdia(String dia) {
		this.dia = dia;
	}

	public String getHoraIni() {
		return this.hora_start.split(":")[0];
	}

	public String getMinIni() {
		return this.hora_start.split(":")[1];
	}
	public String getHoraFin() {
		return this.hora_end.split(":")[0];
	}

	public String getMinFin() {
		return this.hora_end.split(":")[1];
	}
}
