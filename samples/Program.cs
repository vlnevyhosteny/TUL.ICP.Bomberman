using System;

namespace Samples
{
    class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            new CubeWindow().Run(60);
        }
    }
}
