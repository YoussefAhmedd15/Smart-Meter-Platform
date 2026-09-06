import psycopg2


DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "scdc_intelligence"
DB_USER = "postgres"
DB_PASSWORD = "12345678"


connection = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cursor = connection.cursor()

print("Connected to the database successfully.")


# MT514 meter pages

meter_pages = [
    ("01", "Current remaining energy", None),
    ("02", "Current remaining credit", None),
    ("03", "Current remaining days", None),
    ("04", "Cumulative total forward active energy", "No decimal"),
    ("05", "Current month consumption energy", None),
    ("06", "Current step tariff value", None),
    ("07", "Current step tariff No.", None),
    ("08", "Maximum current limit", "Detect single phase"),
    ("09", "Current month consumption credit", None),
    ("10", "Current step number", None),
    ("11-19", "Current step1-9 value", "If no value, display NULL"),
    ("20", "Current step tariff number", None),
    ("21-30", "Current step tariff1-10 value", None),
    ("31", "Current date", None),
    ("32", "Current time", "12 hours format; A-: Morning P-:Afternoon"),
    ("33", "Current week day", "1-7"),
    ("34", "Remain credit alarm limit 1", None),
    ("35", "Remain credit alarm limit 2", None),
    ("36", "Remain credit alarm limit 3", None),
    ("37", "Hoarding threshold", None),
    ("38", "Overdraft threshold not friendly", None),
    ("39", "Active pulse constant", None),
    ("40", "Reactive pulse constant", None),
    ("41", "Serial number of vending system", None),

    ("42", "Customer number high", "8 digits"),
    ("43", "Customer number middle", "6 digits"),
    ("44", "Customer number low", "6 digits"),
    ("45", "Meter number high", "4 digits"),
    ("46", "Meter number middle", "8 digits"),
    ("47", "Meter number low", "8 digits"),
    ("48", "Remain days alarm limit", None),
    ("49", "Cycle display interval", "Unit: seconds"),
    ("50", "Cycle display items number", None),
    ("51", "Actual power on days current month", None),
    ("52", "Average day consumption of last month", None),
    ("53", "Total purchase credit", None),
    ("54", "Purchase times", None),
    ("55", "Terminal cover open times", "Unit: kWh"),
    ("56-57", "Latest terminal cover open date and time", "If there is no event, display NULL"),
    ("58", "Power off times", None),
    ("59-60", "Latest power off date and time", "If there is no event, display NULL"),
    ("61-72", "Last 1-12 month active energy of each month", None),
    ("73-108", "Last 1-12 month Max Demand, happen date and time", None),
    ("109", "Current reverse active energy", None),
    ("110-113", "Alarm reasons", "Details in note1"),
    ("114-116", "Trip reasons", "Details in note2"),
    ("117", "The left time of open cover the relay don't open", "Unit: second"),
    ("118", "Power on times", None),
    ("119-120", "Latest power on date and time", None),
    ("121", "Unbalance limit", None),
    ("122", "The left time of buzzer alarm suspended", None),

    ("123", "The time limit of buzzer alarm suspended", None),
    ("124", "Maximum power limit", None),
    ("125", "Actual continuous over MPL seconds", None),
    ("127", "Actual trip times in one cycle when over MPL", None),
    ("128", "Actual left time of trip when over MPL", None),
    ("129", "Low voltage limit value", None),
    ("131", "Phase A voltage", None),
    ("132", "Phase B voltage", None),
    ("133", "Phase C voltage", None),
    ("134", "Phase A current", None),
    ("135", "Phase B current", None),
    ("136", "Phase C current", None),
    ("137", "Current of neutral line", None),
    ("138", "Phase A fundamental wave voltage", None),
    ("139", "Phase B fundamental wave voltage", None),
    ("140", "Phase C fundamental wave voltage", None),
    ("141", "Phase A fundamental wave current", None),
    ("142", "Phase B fundamental wave current", None),
    ("143", "Phase C fundamental wave current", None),
    ("144", "Total active power", None),
    ("145", "Phase A active power", None),
    ("146", "Phase B active power", None),
    ("147", "Phase C active power", None),
    ("148", "Last 1 minute phase A average power", None),
    ("149", "Last 1 minute phase B average power", None),
    ("150", "Last 1 minute phase C average power", None),
    ("151", "Reactive power", None),
    ("152", "Phase A reactive power", None),
    ("153", "Phase B reactive power", None),
    ("154", "Phase C reactive power", None),
    ("155", "Total power factor", None),
    ("156", "Phase A power factor", None),
    ("157", "Phase B power factor", None),
    ("158", "Phase C power factor", None),
    ("159", "Frequency", None),
    ("160", "Phase disorder happen times", None),
    ("161-162", "The latest phase disorder happen date and time", None),
    ("163", "Reverse happen times", None),
    ("164-165", "The latest reverse happen date and time", None),
    ("166", "Phase loss happen times", None),
    ("167-168", "The latest phase loss happen date and time", None),
    ("169", "Over voltage and low voltage happen times", None),
    ("170-171", "The latest over voltage and low voltage happen date and time", None),
    ("172", "Unbalance happen times", None),
    ("173-174", "The latest unbalance happen date and time", None),
    ("175", "When the latest unbalance happen the unbalance limit", None),
    ("176", "When the latest unbalance happen phase A active power", None),
    ("177", "When the latest unbalance happen phase B active power", None),
    ("178", "When the latest unbalance happen phase C active power", None),
    ("179", "The relay trip times because of the remain credit using up", None),
    ("180-181", "The latest relay trip date and time because of the remain credit using up", None),
    ("182", "Reset happen times", None),
    ("183-184", "The latest reset happen date and time", None),

    ("185", "External battery low voltage happen times", None),
    ("186-187", "The latest external battery low voltage happen date and time", None),
    ("188", "Magnetic disturbance happen times", None),
    ("189-190", "The latest magnetic disturbance happen date and time", None),
    ("191", "Over MPL happen times", None),
    ("192-193", "The latest over MPL happen date and time", None),
    ("194", "Meter cover open times", None),
    ("195-196", "The latest meter cover open date and time", None),
    ("197", "Partially missing neutral happen times", None),
    ("198-199", "The last time partially missing neutral happen date and time", None),
    ("200", "Demand period", None),
    ("201", "Demand period number", None),
    ("202", "Buzzer voice last time", "Unit: 0.01 seconds"),
    ("203", "Buzzer pause voice last time", "Unit: 0.01 seconds"),
    ("204", "Software test finish time", None),
    ("205", "Software version", None),
    ("206", "Hardware version", None),
    ("207", "Current terminal cover status", None),
    ("208", "Total overdraft credit", None),
    ("209", "Total overdraft energy", None),
    ("210", "Power direction", "Details in note3"),
    ("211", "Communication address high", "2 digits"),
    ("212", "Communication address middle", "8 digits"),
    ("213", "Communication address low", "1 digit"),
    ("214", "Billing date", None),
    ("215", "Friendly start time", None),
    ("216", "Friendly finish time", None),

    ("217", "Weekend", "0 means weekend, 1 means work day"),
    ("218", "Prepayment indication", "Bit0/1/2/3/7"),
    ("219", "Friendly indication and TOU holiday indication", "Bit0/1/2/3"),
    ("220", "Offset cover steps", None),
    ("221-230", "Offset value cover from 0-9", None),
    ("231", "TOU tariff number", None),
    ("232-239", "TOU tariff1-8 value", None),
    ("240-241", "TOU time interval switch date and time", None),
    ("242-243", "TOU tariff switch date and time", None),
    ("244-245", "Step switch date and time", None),
    ("246-247", "Step tariff switch date and time", None),
    ("248-249", "Offset switch date and time", None),
    ("250-252", "Each phase total active energy", None),

    ("253", "Left time when pressing the parameter setting button", None),
    ("254", "Protocol of optical", None),
    ("255", "Protocol of RS485", None),
    ("256", "Average power factor", None),
    ("257", "Relay control status", "Disconnect / Connect / NULL"),
    ("258", "Force relay control status left time", None),
    ("259", "Over voltage limit", None),
    ("260", "Standby steps number", None),
    ("261-269", "Standby step1-9 value", None),
    ("270", "Standby step tariff number", None),
    ("271-280", "Standby step tariff 1-10 value", None),
    ("281-290", "Standby offset value", None),
    ("291", "Standby TOU number", None),
    ("292-299", "Standby TOU tariff1-8 value", None),
    ("300-307", "Meter mode word 0-7", "Details in note4"),
    ("308", "Friendly day number", None),
    ("309", "Next friendly date", "YY MM DD, if no display NULL"),
    ("310-339", "Friendly day", None),
    ("340", "Actual power on days last month", None),
    ("341-342", "Open account card insetting date and time", None),
    ("343", "Open account credit", None),
    ("344-352", "Last 3 times purchase record", None),
    ("353-355", "Mend card last charge data and time value", None),
    ("356-357", "Cancel account card insetting date and time", None),
    ("358", "Remain credit before insetting cancel account card", None),
    ("359-360", "Change meter card inserting date and time", None),

    ("361", "Remain credit of change meter card", None),
    ("362-363", "Inset card to remove open cover trip date and time", None),
    ("364", "Inset card to remove open cover trip operator No.", None),
    ("365-366", "Last 1 time remote charge date and time", None),
    ("367", "Last 1 time remote charge credit", None),
    ("368", "Maintenance card insert times", None),
    ("369-370", "Last 1 time maintenance card inset date and time", None),
    ("372", "Friendly time overdraft limit", None),
    ("373", "Load profile record interval", None),
    ("374", "Special radio fees", "Default .002"),
    ("375", "Special radio energy limit", "Default 45kWh"),
    ("376", "Special tariff 1", "Default 0.006 EGP"),
    ("377", "Special tariff energy 1", "Default 10kWh"),
    ("378", "Special tariff 2", "Default 0.003 EGP"),
    ("379", "Special tariff energy 2", "Default 10kWh"),
    ("380", "No consumption for one month the deduct credit", "Default 3 EGP"),
    ("381", "Current month deduction of special radio fees", None),
    ("382", "Current month deduction of special tariff 1", None),
    ("383", "Current month deduction of special tariff 2", None),
    ("384", "Total deduction of special radio fees", None),
    ("385", "Total deduction of special tariff 1", None),
    ("386", "Total deduction of special tariff 2", None),
    ("387", "Total No consumption for one month the deduct credit", None),
    ("388", "Prepayment mode consumption energy", None),
    ("389", "Postpaid mode consumption energy", None),
    ("390", "Prepayment and postpaid indication", "Prepayment: PrEPAY; Credit: POST PAY"),
    ("391", "Current step tariff table No.", None),
    ("392", "Standby step tariff table No.", None),
    ("393-395", "Reverse energy of phase A/B/C", None),
    ("396", "Reactive energy of quadrant 1", None),
    ("397", "Reactive energy of quadrant 2", None),
    ("398", "Reactive energy of quadrant 3", None),
    ("399", "Reactive energy of quadrant 4", None),
    ("400", "The time of no action switch off LCD", None),
    ("401", "Actual max power limit switch times every day", None),
    ("402-465", "Max power limit switch list (current)", "Format: Hour time, current value"),
    ("466", "Billing times", None),
    ("467-478", "Last 1-12 month total active energy", "Less than 9999999.9kWh"),
    ("479-490", "Last 1-12 month active energy of each month", None),
    ("491-502", "Last 1-12 month total active energy", "More than 9999999.9kWh"),
    ("503-504", "Active power demand starting date and time", None),
    ("509-510", "Current demand starting date and time", None),
    ("511-513", "Current month the maximum power demand and happen date and time", None),
    ("535-537", "Current month the Max current demand and happen date and time", None),
    ("538", "Total maximum demand kW", None),
    ("539", "Total maximum demand A", None),
    ("540", "Relay error happen times", None),
    ("541-542", "The latest relay error happen date and time", None),
    ("543", "Relay error kWh", None),
    ("544", "Consumption energy when missing neutral", None),
    ("545", "Standby offset value actual used number", None),
    ("550", "Current TOU tariff value", None),
    ("551", "Current TOU holiday total number", None),
    ("552", "Current TOU week table No.", None),
    ("553", "Current TOU daily table No.", None),

    ("554", "Current TOU tariff No.", None),
    ("555", "Current TOU time interval number", None),
    ("556-569", "Current TOU daily table display", None),
    ("570", "Current TOU week table", None),
    ("571", "Current TOU season number", None),
    ("572-585", "Details of season table", None),
    ("591-598", "Consumption energy of each tariff", None),
    ("599", "Q1+Q2", None),
    ("600", "Q3+Q4", None),
    ("601-612", "Last 1-12 each month power factor", None),
    ("613", "Q1+Q3", None),
    ("614", "Q2+Q4", None),
    ("615", "Q1+Q2+Q3+Q4", None),
    ("616-618", "Phase angle of A/B/C", None),
    ("619", "Angle between phase A voltage and phase B voltage", None),
    ("620", "Angle between phase A voltage and phase C voltage", None),
    ("621", "One phase with current without voltage happen times", None),
    ("622-623", "One phase with current without voltage happen date and time", None),
    ("624", "Calculate neutral current", None),
    ("625", "Totally missing neutral times", None),
    ("626-627", "The last time totally missing neutral happen date and time", None),
    ("628-630", "When change meter the old meter number", None),
    ("631", "Total energy when latest open terminal cover happen", None),
    ("632", "Total consumption when latest power off happen", None),
    ("633", "Total consumption when latest power on happen", None),
    ("634", "Total consumption when latest open top cover happen", None),
    ("635", "Total consumption when latest strong magnetic alarm happen", "Reserve"),
    ("636", "Total consumption when latest battery alarm happen", None),
    ("637", "Total consumption when latest relay error happen", None),
    ("638", "Total consumption when latest reverse happen", None),
    ("639", "Total consumption when latest phases disorder happen", None),
    ("640", "Total consumption when latest loss phase happen", None),
    ("641", "Total consumption when latest total missing neutral happen", None),
    ("642", "Total consumption when latest partial missing neutral happen", None),
    ("643", "Total consumption when latest missing voltage happen", None),
    ("645", "Consumption during Wrong phase sequence", None),
    ("646", "Total consumption during one phase with current without voltage", None),
    ("647", "Total consumption during phase loss", None),
    ("648", "Total consumption money during relay error", None),
    ("649", "This month reactive energy", None),
    ("650-661", "Last 1-12 month reactive energy", None),
    ("662", "Reactive rollover number", None),
    ("663", "Billing offset numbers", None),
    ("664-673", "Current billing offset table", None),
    ("674", "Overdraft energy", None),
    ("675", "Overdraft credit", None),
    ("676", "Average power factor one year", None),
    ("677", "Monthly consumption limit 1", None),
    ("678", "Monthly consumption limit 2", None),
    ("679", "Monthly special fee", None),
    ("680", "Currently monthly overdraft limit", None),
    ("681", "Monthly remain credit after deduct special fee", None),
    ("682", "Monthly overdraft active limit", None),
    ("683", "Buzzer keep silent start time", None),
    ("684", "Buzzer keep silent end time", None)
]


# MT514 error codes

meter_errors = [
    ("01", "Data cannot be read"),
    ("02-30", "Data frame verification error"),
    ("31-35", "32K read card data frame verification error"),
    ("36", "32kB card index error"),
    ("37", "32kB card password protect area CRC check error"),
    ("38", "32kB card set area CRC check error"),
    ("39", "32KB card password check error"),
    ("40", "Card type error"),
    ("41", "The meter type data is not 3 phase in the card"),
    ("42", "Cannot support prepay fee"),
    ("43", "Vending system serial number error"),
    ("44", "Purchase credit too more over 999999.99"),
    ("45", "Customer No error"),
    ("46", "Meter No error (this card already turn back other customers information)"),
    ("47", "Meter No error when the meter/card number is not right"),
    ("48", "Preset energy of each phase over 10000000kWh"),
    ("49", "Credit is more than 999999.99"),
    ("50", "Initialization card return data error"),
    ("51-55", "Pull out card too early before the meter finishing reading"),
    ("57", "Pull out card too early, when insetting 32K read card"),
    ("58", "Pull out card too early, when copy the data from meter to card"),
    ("59", "Pull out card too early, when copy the data from card to meter"),
    ("60-63", "CPU Card approved error"),
    ("64", "32kB card user No error"),
    ("70", "The lead seal button is not be pressed"),
    ("71", "Status error, the meter cannot accept purchase card before open account"),
    ("72", "The meter is already cancel account"),
    ("73", "Relay check of last time is not finish"),
    ("74", "Address back to card over the Max address"),
    ("75", "The meter has been open account cannot accept setting card"),
    ("76", "Reserved"),
    ("77", "Reserved"),
    ("78", "Data back to card is bad position, the first 64 byte of CPU Card"),
    ("79", "Data back to card is bad position, over 0x3D0"),
    ("80", "The value in the card add the remain credit in the meter is too high"),
    ("81", "Purchase times error: times in the card is more than times in the meter"),
    ("82", "Purchase times error: times in the card is less than times in the meter"),
    ("83", "Terminal cover is not covered well when removing open cover alarm"),
    ("84", "Meter cover is not covered well when removing open cover alarm"),
    ("85", "Meter cover and terminal cover are not covered well when removing open cover alarm"),
    ("86", "The lead seal button is not pressed when copy the data from meter to card"),
    ("87", "The lead seal button is not pressed when copy the data from card to meter"),
    ("88", "Pull out card too early when copy data from meter to card and meter number is different"),
    ("89", "Pull out card too early when copy data from card to meter and meter number is different"),
    ("90", "Still over MPL when removing over MPL alarm"),
    ("91", "Over limit time"),
    ("92", "Not 32KB change card, old meter is still good meter"),
    ("93", "Event still exist"),
    ("94", "Not 32KB change card, old meter is damaged meter"),
    ("95", "Not press the program button when inset change card"),
    ("96", "The firmware of old meter is too old"),
    ("97", "The change meter card already used"),
    ("98", "Pull out too early when inset change meter card")
]


# Clear old data

cursor.execute(
    "TRUNCATE TABLE meter_pages RESTART IDENTITY CASCADE"
)

cursor.execute(
    "TRUNCATE TABLE meter_error_codes RESTART IDENTITY CASCADE"
)


# Insert meter pages

cursor.executemany(
    """
    INSERT INTO meter_pages (
        item_no,
        item_name,
        remark
    )
    VALUES (%s, %s, %s)
    """,
    meter_pages
)


# Insert meter errors

cursor.executemany(
    """
    INSERT INTO meter_error_codes (
        error_code,
        description
    )
    VALUES (%s, %s)
    """,
    meter_errors
)


connection.commit()


# Validate

cursor.execute("""
    SELECT COUNT(*)
    FROM meter_pages
""")

page_count = cursor.fetchone()[0]


cursor.execute("""
    SELECT COUNT(*)
    FROM meter_error_codes
""")

error_count = cursor.fetchone()[0]


print()
print("MT514 DATA LOAD COMPLETED")
print("------------------------------------------")
print("Meter pages inserted:", page_count)
print("Meter error codes inserted:", error_count)


cursor.close()
connection.close()

print()
print("Database connection closed.")
print("Done.")