// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "Framework/Commands/Commands.h"
#include "City_Generation_Tool_BarStyle.h"

class FCity_Generation_Tool_BarCommands : public TCommands<FCity_Generation_Tool_BarCommands>
{
public:

	FCity_Generation_Tool_BarCommands()
		: TCommands<FCity_Generation_Tool_BarCommands>(TEXT("City_Generation_Tool_Bar"), NSLOCTEXT("Contexts", "City_Generation_Tool_Bar", "City_Generation_Tool_Bar Plugin"), NAME_None, FCity_Generation_Tool_BarStyle::GetStyleSetName())
	{
	}

	// TCommands<> interface
	virtual void RegisterCommands() override;

public:
	TSharedPtr< FUICommandInfo > PluginAction;
};
