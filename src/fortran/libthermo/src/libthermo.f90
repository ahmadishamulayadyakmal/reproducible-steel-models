module libthermo
  !! Minimal thermodynamic/numerical kernel library for the portfolio.
  !! Physics kernels (mesh, FVM, enthalpy-porosity) are added in W09-W13.
  implicit none
  private

  integer, parameter, public :: dp = kind(1.0d0)
  character(len=*), parameter, public :: version = "0.1.0"

  public :: kelvin_from_celsius, celsius_from_kelvin

  real(dp), parameter :: zero_celsius_in_kelvin = 273.15_dp

contains

  pure function kelvin_from_celsius(t_c) result(t_k)
    !! Convert degrees Celsius to kelvin. SI is the internal convention.
    real(dp), intent(in) :: t_c
    real(dp) :: t_k

    t_k = t_c + zero_celsius_in_kelvin
  end function kelvin_from_celsius

  pure function celsius_from_kelvin(t_k) result(t_c)
    !! Convert kelvin to degrees Celsius.
    real(dp), intent(in) :: t_k
    real(dp) :: t_c

    t_c = t_k - zero_celsius_in_kelvin
  end function celsius_from_kelvin

end module libthermo
