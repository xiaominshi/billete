
public class EscalaTime {
	private int hora;
	private int minuto;
	private String lugar;
	public int getHora() {
		return hora;
	}
	public void setHora(int hora) {
		this.hora = hora;
	}
	public int getMinuto() {
		return minuto;
	}
	public void setMinuto(int minuto) {
		this.minuto = minuto;
	}
	public String getLugar() {
		return lugar;
	}
	public void setLugar(String lugar) {
		this.lugar = lugar;
	}
	public EscalaTime(int hora, int minuto, String lugar) {
		super();
		this.hora = hora;
		this.minuto = minuto;
		this.lugar = lugar;
	}
	

}
