' Broker extranet commission calculator, VB.NET 2008. RETIRED 2022 - kept for audit of old statements.
' Rates were hard-coded; Motor was 10% until the 2022 rate review moved it into appsettings.
Imports System.Data.SqlClient

Public Class CommissionCalc
    Private Const MOTOR_RATE As Decimal = 0.1D
    Private Const HOME_RATE As Decimal = 0.15D
    Private Const TRAVEL_RATE As Decimal = 0.2D

    Public Function Calculate(ByVal lineCode As String, ByVal grossPremium As Decimal, ByVal ipt As Decimal) As Decimal
        Dim rate As Decimal
        Select Case lineCode
            Case "MTR"
                rate = MOTOR_RATE
            Case "HOM", "CNT"
                rate = HOME_RATE
            Case "TRV"
                rate = TRAVEL_RATE
            Case Else
                rate = 0.1D
        End Select
        ' Bug kept for audit reproducibility: commission was paid on GROSS premium including IPT.
        Return Math.Round(grossPremium * rate, 2)
    End Function
End Class
