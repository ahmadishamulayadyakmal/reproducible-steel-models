program test_libthermo
  !! Dependency-free smoke test so `fpm test` works with no network access.
  !! A test framework will be introduced with the solver tests in W09.
  use libthermo, only : dp, version, kelvin_from_celsius, celsius_from_kelvin
  implicit none

  real(dp), parameter :: tol = 1.0e-12_dp

  call check_close(kelvin_from_celsius(0.0_dp), 273.15_dp, tol, "0 C -> 273.15 K")
  call check_close(celsius_from_kelvin(273.15_dp), 0.0_dp, tol, "273.15 K -> 0 C")
  call check_close(celsius_from_kelvin(kelvin_from_celsius(727.0_dp)), 727.0_dp, &
                   tol, "round trip at 727 C")

  if (trim(version) /= "0.1.0") then
    print *, "FAIL: unexpected libthermo version"
    error stop 1
  end if

  print *, "test_libthermo: 3 assertions passed"

contains

  subroutine check_close(got, expected, tolerance, label)
    real(dp), intent(in) :: got, expected, tolerance
    character(len=*), intent(in) :: label

    if (abs(got - expected) > tolerance) then
      print *, "FAIL: ", trim(label)
      print *, "  got = ", got, " expected = ", expected
      error stop 1
    end if
  end subroutine check_close

end program test_libthermo
