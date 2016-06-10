<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 
<xsl:template match="/">
<HTML>
<BODY>
    <xsl:apply-templates/>
</BODY>
</HTML>
</xsl:template>

<xsl:template match="solution">
<TABLE BORDER="1">
<TR>
	<TD>State</TD>
	<TD>Park Name</TD>
	<TD>Trail Name</TD>
	<TD>Location</TD>
	<TD>Arrival Date</TD>
	<TD>LOS (days)</TD>
	<TD>Departure Date</TD>
	<TD>Expected Weather</TD>
	<TD>Distance to next location (mi)</TD>
</TR>
<TR>
<TD/><TD/><TD><xsl:value-of select="start_location/text()"/></TD><TD/><TD/><TD/><TD><xsl:value-of select="start_location/departureDate/text()"/></TD><TD/><TD><xsl:value-of select="format-number(start_location/distance div 1609,'0.0')"/></TD>
</TR>
<xsl:for-each select="location">
<TR>
	<TD><xsl:value-of select="state/text()"/></TD>
	<TD><xsl:value-of select="parkName/text()"/></TD>      
	<TD><xsl:value-of select="trailName/text()"/></TD>
	<TD><xsl:value-of select="trailhead/text()"/></TD>
	<TD><xsl:value-of select="arrivalDate/text()"/></TD>
	<TD><xsl:value-of select="los/text()"/></TD>
	<TD><xsl:value-of select="departureDate/text()"/></TD>
	<TD><xsl:value-of select="expectedWeather/text()"/></TD>
	<TD><xsl:value-of select="format-number(distance div 1609,'0.0')"/></TD>

</TR>
</xsl:for-each>
<TD/><TD/><TD><xsl:value-of select="end_location/text()"/></TD><TD><xsl:value-of select="end_location/arrival_date/text()"/></TD><TD/><TD/><TD/><TD/>
</TABLE>
</xsl:template>
</xsl:stylesheet>
