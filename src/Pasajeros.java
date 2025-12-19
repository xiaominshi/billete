
public class Pasajeros {
	private String name;
	private String id;
	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	private String pasaporte;
	private String pasaporte_ini;
	private String pasaporte_fin;
	private String genero;
	private String num_billete;
	
	
	public String getNum_billete() {
		return num_billete;
	}

	public void setNum_billete(String num_billete) {
		this.num_billete = num_billete;
	}

	public String getPasaporte() {
		return pasaporte;
	}

	public void setPasaporte(String pasaporte) {
		this.pasaporte = pasaporte;
	}

	public String getPasaporte_ini() {
		return pasaporte_ini;
	}

	public void setPasaporte_ini(String pasaporte_ini) {
		this.pasaporte_ini = pasaporte_ini;
	}

	public String getPasaporte_fin() {
		return pasaporte_fin;
	}

	public void setPasaporte_fin(String pasaporte_fin) {
		this.pasaporte_fin = pasaporte_fin;
	}

	public String getGenero() {
		return genero;
	}

	public void setGenero(String genero) {
		this.genero = genero;
	}

	public Pasajeros(String name) {
		this.name = name;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}
	

}
