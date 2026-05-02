// Copyright Epic Games, Inc. All Rights Reserved.

#include "City_Generation_Tool_BarCommands.h"

#define LOCTEXT_NAMESPACE "FCity_Generation_Tool_BarModule"

void FCity_Generation_Tool_BarCommands::RegisterCommands()
{
	UI_COMMAND(PluginAction, "City_Generation_Tool_Bar", "Execute City_Generation_Tool_Bar action", EUserInterfaceActionType::Button, FInputChord());
}

#undef LOCTEXT_NAMESPACE
