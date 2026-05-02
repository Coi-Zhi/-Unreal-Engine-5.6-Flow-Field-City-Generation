// Copyright Epic Games, Inc. All Rights Reserved.

#include "City_Generation_Tool_BarStyle.h"
#include "City_Generation_Tool_Bar.h"
#include "Framework/Application/SlateApplication.h"
#include "Styling/SlateStyleRegistry.h"
#include "Slate/SlateGameResources.h"
#include "Interfaces/IPluginManager.h"
#include "Styling/SlateStyleMacros.h"

#define RootToContentDir Style->RootToContentDir

TSharedPtr<FSlateStyleSet> FCity_Generation_Tool_BarStyle::StyleInstance = nullptr;

void FCity_Generation_Tool_BarStyle::Initialize()
{
	if (!StyleInstance.IsValid())
	{
		StyleInstance = Create();
		FSlateStyleRegistry::RegisterSlateStyle(*StyleInstance);
	}
}

void FCity_Generation_Tool_BarStyle::Shutdown()
{
	FSlateStyleRegistry::UnRegisterSlateStyle(*StyleInstance);
	ensure(StyleInstance.IsUnique());
	StyleInstance.Reset();
}

FName FCity_Generation_Tool_BarStyle::GetStyleSetName()
{
	static FName StyleSetName(TEXT("City_Generation_Tool_BarStyle"));
	return StyleSetName;
}


const FVector2D Icon16x16(16.0f, 16.0f);
const FVector2D Icon20x20(20.0f, 20.0f);

TSharedRef< FSlateStyleSet > FCity_Generation_Tool_BarStyle::Create()
{
	TSharedRef< FSlateStyleSet > Style = MakeShareable(new FSlateStyleSet("City_Generation_Tool_BarStyle"));
	Style->SetContentRoot(IPluginManager::Get().FindPlugin("City_Generation_Tool_Bar")->GetBaseDir() / TEXT("Resources"));

	Style->Set("City_Generation_Tool_Bar.PluginAction", new IMAGE_BRUSH_SVG(TEXT("PlaceholderButtonIcon"), Icon20x20));
	return Style;
}

void FCity_Generation_Tool_BarStyle::ReloadTextures()
{
	if (FSlateApplication::IsInitialized())
	{
		FSlateApplication::Get().GetRenderer()->ReloadTextureResources();
	}
}

const ISlateStyle& FCity_Generation_Tool_BarStyle::Get()
{
	return *StyleInstance;
}
