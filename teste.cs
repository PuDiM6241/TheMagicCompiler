using System;

class Program {
    static void Main() {
        // "Este eh um programa de teste"
        long yggdrasil = 30;
        int contador = 0;
        Console.WriteLine(yggdrasil);
        if (contador <= 10) {
            Console.WriteLine("Ganhei");
        } else if (contador > 21) {
            Console.WriteLine("perdi");
        } else {
            Console.WriteLine("Empate");
        }
        double peso = 11;
        while (peso > 5) {
            if (peso <= 10) {
                Console.WriteLine("Dentro do range");
            } else {
                Console.WriteLine("Fora do range");
            }
            peso--;
        }
        for (int i = 0; i < 5; i++) {
            Console.WriteLine(i);
        }
    }
}